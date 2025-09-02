document.addEventListener('DOMContentLoaded', function() {
    const deliveryWeekSelect = document.getElementById('delivery-week');
    const weekQuantityInput = document.getElementById('week-quantity');
    const addWeekBtn = document.getElementById('add-week-btn');
    const availabilityInfo = document.getElementById('week-availability-info');
    const availabilityText = document.getElementById('availability-text');
    const availabilityBadge = document.getElementById('availability-badge');
    
    if (!deliveryWeekSelect || !weekQuantityInput || !addWeekBtn) return;

    const selectedWeeksContainer = document.getElementById('selected-weeks-container');
    const selectedWeeksList = document.getElementById('selected-weeks-list');
    const orderSummary = document.getElementById('order-summary');
    const totalEggsElement = document.getElementById('total-eggs');
    const totalPriceElement = document.getElementById('total-price');
    const weekSelectionsInputs = document.getElementById('week-selections-inputs');
    const pendingSelection = document.getElementById('pending-selection');
    const finalSubmitBtn = orderSummary?.querySelector('button[type="submit"]');

    const priceMeta = document.querySelector('meta[name="product-price"]');
    const productPrice = priceMeta ? parseFloat(priceMeta.content) : 0;
    const minQuantityPerWeek = parseInt(weekQuantityInput.min || '1');
    const maxQuantityPerWeek = parseInt(weekQuantityInput.max || '100');
    
    let selectedWeeks = {}; // { weekId: { quantity: x, label: 'Week ending...' } }
    let currentMaxAvailableForWeek = 0;

    // --- Event Listeners ---
    deliveryWeekSelect.addEventListener('change', handleWeekChange);
    weekQuantityInput.addEventListener('input', handleQuantityChange);
    addWeekBtn.addEventListener('click', addSelectedWeek);

    // --- Functions ---
    function handleWeekChange() {
        const selectedOption = deliveryWeekSelect.options[deliveryWeekSelect.selectedIndex];
        const weekId = selectedOption.value;
        
        if (weekId) {
            currentMaxAvailableForWeek = parseInt(selectedOption.dataset.available || '0');
            availabilityInfo.style.display = 'block';
            updateAvailabilityDisplay();
            validateSelection();
        } else {
            availabilityInfo.style.display = 'none';
            currentMaxAvailableForWeek = 0;
            addWeekBtn.disabled = true;
        }
    }

    function handleQuantityChange() {
        validateSelection();
    }
    
    window.changeWeekQuantity = function(amount) {
        let currentValue = parseInt(weekQuantityInput.value || '0');
        let newValue = currentValue + amount;
        // Clamp value between min and max allowed for the input itself
        newValue = Math.max(minQuantityPerWeek, Math.min(maxQuantityPerWeek, newValue));
        weekQuantityInput.value = newValue;
        handleQuantityChange(); // Trigger validation
    }

    function validateSelection() {
        const weekId = deliveryWeekSelect.value;
        const quantity = parseInt(weekQuantityInput.value || '0');
        
        if (!weekId || isNaN(quantity)) {
            addWeekBtn.disabled = true;
            if (pendingSelection) pendingSelection.textContent = '';
            return;
        }

        const availableForSelection = currentMaxAvailableForWeek;
        
        // Check basic quantity rules
        if (quantity < minQuantityPerWeek || quantity > maxQuantityPerWeek) {
             weekQuantityInput.classList.add('is-invalid');
             addWeekBtn.disabled = true;
             if (pendingSelection) pendingSelection.textContent = '';
             return;
        } else {
             weekQuantityInput.classList.remove('is-invalid');
        }
        
        // Check availability for the selected week
        if (quantity > availableForSelection) {
            addWeekBtn.disabled = true;
            if (pendingSelection) pendingSelection.textContent = '';
        } else {
            addWeekBtn.disabled = false;
            // Show a brief summary of what will be added
            const selectedOption = deliveryWeekSelect.options[deliveryWeekSelect.selectedIndex];
            const weekLabel = selectedOption ? selectedOption.text.split(' (')[0] : '';
            if (pendingSelection) pendingSelection.textContent = weekLabel ? `Pending: ${weekLabel} • ${quantity} eggs` : '';
        }
    }

    function updateAvailabilityDisplay() {
        const selectedOption = deliveryWeekSelect.options[deliveryWeekSelect.selectedIndex];
        const weekId = selectedOption.value;
        if (!weekId) return;

        const available = currentMaxAvailableForWeek; 
        availabilityText.textContent = `Available for ${selectedOption.text.split(' (')[0]}: ${available} eggs.`;
        
        if (available >= minQuantityPerWeek) {
            availabilityBadge.textContent = 'Available';
            availabilityBadge.className = 'badge bg-success';
        } else {
            availabilityBadge.textContent = 'Unavailable';
            availabilityBadge.className = 'badge bg-danger';
        }
    }
    
    function addSelectedWeek() {
        const weekId = deliveryWeekSelect.value;
        const quantity = parseInt(weekQuantityInput.value || '0');
        const selectedOption = deliveryWeekSelect.options[deliveryWeekSelect.selectedIndex];
        const weekLabel = selectedOption.text.split(' (')[0]; // Get clean label
        const availableBeforeAdd = parseInt(selectedOption.dataset.available || '0');

        if (!weekId || isNaN(quantity) || quantity < minQuantityPerWeek || quantity > availableBeforeAdd) {
            return; 
        }

        // Update selectedWeeks object
        if (selectedWeeks[weekId]) {
            selectedWeeks[weekId].quantity = quantity;
        } else {
            selectedWeeks[weekId] = { quantity: quantity, label: weekLabel };
        }

        // Update availability in dropdown
        const newAvailable = availableBeforeAdd - quantity;
        selectedOption.dataset.available = newAvailable;
        selectedOption.text = `${weekLabel} (${newAvailable} eggs available)`;
        currentMaxAvailableForWeek = newAvailable; // Update current context

        // Update UI
        updateSelectedWeeksList();
        updateOrderSummary();
        updateHiddenInputs();

        // Reset selection controls
        deliveryWeekSelect.value = '';
        weekQuantityInput.value = minQuantityPerWeek;
        availabilityInfo.style.display = 'none';
        addWeekBtn.disabled = true;
        if (pendingSelection) pendingSelection.textContent = '';
    }

    function updateSelectedWeeksList() {
        selectedWeeksList.innerHTML = ''; // Clear current list
        const weekIds = Object.keys(selectedWeeks);
        
        if (weekIds.length === 0) {
            selectedWeeksContainer.style.display = 'none';
            orderSummary.style.display = 'none';
            return;
        }

        selectedWeeksContainer.style.display = 'block';
        orderSummary.style.display = 'block';

        // Toggle empty state helper inside the container if present
        const emptyMsg = selectedWeeksContainer.querySelector('.empty-selection-message');
        if (emptyMsg) emptyMsg.style.display = weekIds.length === 0 ? 'block' : 'none';

        for (const weekId of weekIds) {
            const week = selectedWeeks[weekId];
            const li = document.createElement('li');
            li.className = 'list-group-item selected-week-row d-flex align-items-center justify-content-between';

            // Left: label
            const left = document.createElement('div');
            left.className = 'review-left';
            const weekText = document.createElement('span');
            weekText.className = 'review-week-label';
            weekText.textContent = week.label;
            left.appendChild(weekText);

            // Middle: quantity badge
            const middle = document.createElement('div');
            middle.className = 'review-middle';
            const quantityBadge = document.createElement('span');
            quantityBadge.className = 'badge bg-primary rounded-pill';
            quantityBadge.textContent = `${week.quantity} eggs`;
            middle.appendChild(quantityBadge);

            // Right: remove button in its own small area
            const right = document.createElement('div');
            right.className = 'review-remove';
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-outline-danger btn-icon';
            removeBtn.setAttribute('aria-label', `Remove ${week.label}`);
            removeBtn.innerHTML = '&times;';
            removeBtn.onclick = () => removeWeekSelection(weekId);
            right.appendChild(removeBtn);

            li.appendChild(left);
            li.appendChild(middle);
            li.appendChild(right);
            selectedWeeksList.appendChild(li);
        }
    }
    
    function removeWeekSelection(weekIdToRemove) {
        if (!selectedWeeks[weekIdToRemove]) return;

        const removedQuantity = selectedWeeks[weekIdToRemove].quantity;
        delete selectedWeeks[weekIdToRemove];

        // Restore availability in dropdown
        for (let i = 0; i < deliveryWeekSelect.options.length; i++) {
            const option = deliveryWeekSelect.options[i];
            if (option.value === weekIdToRemove) {
                const currentAvailable = parseInt(option.dataset.available || '0');
                const newAvailable = currentAvailable + removedQuantity;
                const weekLabel = option.text.split(' (')[0];
                option.dataset.available = newAvailable;
                option.text = `${weekLabel} (${newAvailable} eggs available)`;
                if (deliveryWeekSelect.value === weekIdToRemove) {
                    currentMaxAvailableForWeek = newAvailable;
                    handleWeekChange();
                }
                break;
            }
        }
        
        // Update UI
        updateSelectedWeeksList();
        updateOrderSummary();
        updateHiddenInputs();
    }

    function updateHiddenInputs() {
        weekSelectionsInputs.innerHTML = '';
        for (const weekId in selectedWeeks) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = weekId; // Set name directly to the week ID (e.g., '2025-12')
            input.value = selectedWeeks[weekId].quantity;
            weekSelectionsInputs.appendChild(input);
        }
    }

    function calculateTotalEggs() {
        return Object.values(selectedWeeks).reduce((sum, week) => sum + week.quantity, 0);
    }

    function updateOrderSummary() {
        const totalEggs = calculateTotalEggs();
        const totalPrice = totalEggs * productPrice;

        totalEggsElement.textContent = totalEggs;
        totalPriceElement.textContent = formatCurrency(totalPrice);

        if (finalSubmitBtn) {
            const isDisabled = totalEggs === 0;
            finalSubmitBtn.disabled = isDisabled;
            if (isDisabled) {
                finalSubmitBtn.setAttribute('aria-disabled', 'true');
            } else {
                finalSubmitBtn.removeAttribute('aria-disabled');
            }
        }
    }

    function formatCurrency(amount) {
        return '$' + amount.toFixed(2);
    }
    
    // Initial setup if needed
    handleWeekChange();
});
