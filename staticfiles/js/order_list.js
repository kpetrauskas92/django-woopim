document.addEventListener("DOMContentLoaded", function () {
    const dateInput = document.getElementById("order-date");
    const syncBtn = document.getElementById("syncOrders");
    const cancelBtn = document.getElementById("cancelSync");
    let isSyncing = false;

    function updateSyncStatus(data) {
        const statusContainer = document.getElementById("sync-status-container");
        const statusClass = data.status === "error" ? "text-red-500" : "text-green-500";
        statusContainer.innerHTML = `<div class="${statusClass}">${data.message}</div>`;
    }

    // Initialize max date
    const today = new Date();
    if (today.getFullYear() === 2025) {
        dateInput.max = today.toISOString().split('T')[0];
    }

    // Enable/disable sync button based on date selection
    function updateButtonState() {
        syncBtn.disabled = !dateInput.value;
    }

    // Initial state setup
    updateButtonState();

    // Event listeners
    dateInput.addEventListener("change", updateButtonState);
    dateInput.addEventListener("input", updateButtonState);

    // Format date to ISO string (YYYY-MM-DD)
    function formatDate(inputDate) {
        return new Date(inputDate).toISOString().split('T')[0];
    }

    // Sync button handler
    syncBtn.addEventListener("click", async function() {
        if (!dateInput.value || isSyncing) return;

        isSyncing = true;
        const formattedDate = formatDate(dateInput.value);
        
        // Update UI
        syncBtn.disabled = true;
        document.getElementById("syncText").textContent = "Syncing...";
        document.getElementById("syncLoading").classList.remove("hidden");
        cancelBtn.classList.remove("hidden");

        try {
            const response = await fetch("/scraper/sync-rv-orders/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ selected_date: formattedDate })
            });
            
            const data = await response.json();
            updateSyncStatus(data);
            
            if (data.status === "success") {
                dateInput.value = "";
            }
        } catch (error) {
            updateSyncStatus({ message: "❌ Network error!", status: "error" });
        } finally {
            isSyncing = false;
            updateButtonState();
            document.getElementById("syncText").textContent = "Sync RV Orders";
            document.getElementById("syncLoading").classList.add("hidden");
            cancelBtn.classList.add("hidden");
        }
    });

    // Cancel button handler
    cancelBtn.addEventListener("click", async function() {
        try {
            const response = await fetch("/scraper/cancel-sync/", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            const data = await response.json();
            updateSyncStatus(data);
        } catch (error) {
            updateSyncStatus({ message: "❌ Failed to cancel sync", status: "error" });
        }
    });

    // WooCommerce Sync Orders
    const wooSyncBtn = document.getElementById("syncWooOrders");
    wooSyncBtn.addEventListener("click", function() {
        const wooSyncText = document.getElementById("wooSyncText");
        const wooSyncLoading = document.getElementById("wooSyncLoading");

        wooSyncText.innerText = "Syncing... Please Wait";
        wooSyncLoading.classList.remove("hidden");

        fetch("/orders/sync-woocommerce-orders/", { 
            method: "POST", 
            headers: { "X-CSRFToken": getCookie("csrftoken") } 
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            wooSyncText.innerText = "Sync WooCommerce Orders";
            wooSyncLoading.classList.add("hidden");
        })
        .catch(error => {
            alert("❌ Sync Failed! " + error);
            wooSyncText.innerText = "Sync WooCommerce Orders";
            wooSyncLoading.classList.add("hidden");
        });
    });

    // CSRF Token Helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});

// Open Sync Logs Modal with HTMX trigger
function openSyncLogModal() {
    let modal = document.getElementById("syncLogModal");
    modal.showModal();
    htmx.trigger("#sync-log-content", "revealed");
}
