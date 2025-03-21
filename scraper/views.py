import os
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .utils import setup_driver, scrape_orders, cancel_sync, is_sync_canceled

SYNC_IN_PROGRESS = False
LOG_FILE = os.path.join(settings.BASE_DIR, "logs", "rv_sync.log")

@csrf_exempt
def sync_rv_orders(request):
    """
    Starts the Retail Vista sync process and logs everything properly.
    Ensures only one sync can happen at a time.
    """
    global SYNC_IN_PROGRESS

    if SYNC_IN_PROGRESS:
        return JsonResponse({"message": "⚠️ Sync already in progress.", "status": "warning"})

    logs = []
    sync_start_time = now().strftime("%Y-%m-%d %H:%M:%S")
    driver = None  # Ensure driver is initialized

    def log_message(message):
        """ Helper function to store and print log messages. """
        logs.append(message)
        print(message)  # Output to terminal

    if request.method == "POST":
        try:
            # ✅ Check if request body is empty
            if not request.body:
                log_message("❌ No data received!")
                return JsonResponse({"message": "❌ No data received!", "status": "error"})

            # ✅ Try to parse JSON safely
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                log_message("❌ Invalid JSON format received!")
                return JsonResponse({"message": "❌ Invalid JSON format!", "status": "error"})

            selected_date = data.get("selected_date")  # Retrieve date from frontend

            if not selected_date:
                log_message("❌ No date provided in request!")
                return JsonResponse({"message": "❌ No date provided!", "status": "error"})

            log_message(f"\n================== SYNC START: {sync_start_time} ==================\n")
            log_message(f"📅 Selected Sync Date: {selected_date}")

            SYNC_IN_PROGRESS = True  # Set flag to prevent duplicate syncs
            driver = setup_driver()  # Start WebDriver

            # ✅ Pass the selected date to the Selenium function
            result = scrape_orders(log_message, driver, is_sync_canceled, selected_date)

            sync_message = result.get("message", "✅ Sync completed!")
            status = "success"

        except Exception as e:
            sync_message = f"❌ Sync failed: {str(e)}"
            status = "error"
            log_message(sync_message)

        finally:
            if driver:  # ✅ Ensure WebDriver quits only if initialized
                driver.quit()
            SYNC_IN_PROGRESS = False  # Reset flag

            # ✅ Append logs to a file
            with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                log_file.write("\n".join(logs) + "\n")

            log_message(f"\n================== SYNC END: {now().strftime('%Y-%m-%d %H:%M:%S')} ==================\n")

        return JsonResponse({"message": sync_message, "status": status})

    return JsonResponse({"message": "❌ Invalid request method.", "status": "error"}, status=400)


@csrf_exempt
def cancel_sync_view(request):
    """
    Cancels an ongoing sync instantly.
    """
    if request.method == "POST":
        cancel_sync()  # Set cancellation flag
        return JsonResponse({"message": "❌ Sync Canceled!", "status": "error"})

    return JsonResponse({"message": "❌ Invalid request method.", "status": "error"}, status=400)


def view_sync_log(request):
    """
    Returns the sync log file formatted for HTML display, with the newest logs first.
    """
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as log_file:
            log_entries = log_file.read().strip().split("\n\n================== SYNC START: ")  # Split logs by sessions

        log_entries = [f" {entry}" for entry in log_entries if entry.strip()]
        log_entries.reverse()  # Show the latest log at the top

        formatted_logs = ""
        for entry in log_entries:
            lines = entry.strip().split("\n")
            title = lines[0] if lines else "📜 Sync Log"
            log_body = "\n".join(lines[1:]).strip()

            formatted_logs += f"""
            <div tabindex="0" class="collapse collapse-arrow bg-base-100 border border-gray-300 mb-2">
                <div class="collapse-title font-semibold flex justify-center">{title}</div>
                <div class="collapse-content text-sm p-2">
                    <pre class="whitespace-pre-wrap">{log_body}</pre>
                </div>
            </div>
            """

        return HttpResponse(formatted_logs)

    return HttpResponse("<p class='text-center p-4'>No sync logs found.</p>")