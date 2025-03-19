document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the product page with date picker
    const datePicker = document.getElementById('date-picker');
    if (!datePicker) return;

    // Get the available weeks data from the hidden input
    const availableWeeksElement = document.getElementById('available-weeks-data');
    if (!availableWeeksElement) return;

    // Function to initialize flatpickr with retries
    function initializeFlatpickr() {
        if (typeof flatpickr === 'undefined') {
            console.log('Flatpickr not loaded yet, retrying in 100ms...');
            setTimeout(initializeFlatpickr, 100);
            return;
        }
        
        try {
            // Parse the available weeks data
            const availableWeeks = JSON.parse(availableWeeksElement.value);
            
            // Create a map of available weeks for easy lookup
            const weeksMap = {};
            availableWeeks.forEach(function(week) {
                weeksMap[week.id] = week;
            });

            // Helper function to format date as YYYY-MM-DD
            function formatDate(date) {
                const d = new Date(date);
                let month = '' + (d.getMonth() + 1);
                let day = '' + d.getDate();
                const year = d.getFullYear();
                
                if (month.length < 2) month = '0' + month;
                if (day.length < 2) day = '0' + day;
                
                return [year, month, day].join('-');
            }

            // Initialize flatpickr with inline calendar
            const calendar = flatpickr(datePicker, {
                inline: true,
                static: true,
                mode: "single",
                dateFormat: "Y-m-d",
                minDate: "today",
                maxDate: new Date().fp_incr(90),
                disable: [
                    function(date) {
                        // Only enable dates that match our available weeks
                        const dateStr = formatDate(date);
                        return !availableWeeks.some(function(week) { 
                            return week.id === dateStr; 
                        });
                    }
                ],
                onChange: function(selectedDates, dateStr) {
                    if (selectedDates.length > 0) {
                        const weekId = formatDate(selectedDates[0]);
                        
                        // Update hidden input with selected date
                        const selectedWeekId = document.getElementById('selected-week-id');
                        if (selectedWeekId) {
                            selectedWeekId.value = weekId;
                        }
                        
                        // Update availability information
                        updateAvailabilityInfo(weekId, weeksMap);
                        
                        // Validate add to order button
                        validateAddToOrder(weekId, weeksMap);
                    }
                }
            });

            // Update availability information for selected week
            function updateAvailabilityInfo(weekId, weeksMap) {
                const weekAvailabilityInfo = document.getElementById('week-availability-info');
                const availabilityText = document.getElementById('availability-text');
                const availabilityBadge = document.getElementById('availability-badge');
                const quantityInput = document.getElementById('quantity-input');
                const addToOrderBtn = document.getElementById('add-to-order-btn');
                
                if (weekId && weeksMap[weekId]) {
                    const week = weeksMap[weekId];
                    weekAvailabilityInfo.style.display = 'block';
                    
                    // Update availability text and badge
                    availabilityText.textContent = week.available + " of " + week.total + " eggs available";
                    
                    // Set max quantity to available eggs
                    quantityInput.max = week.available;
                    if (parseInt(quantityInput.value) > week.available) {
                        quantityInput.value = week.available;
                    }
                    
                    // Update badge based on status
                    availabilityBadge.textContent = week.status_text || '';
                    availabilityBadge.className = 'availability-badge';
                    
                    if (week.status === 'sold_out') {
                        availabilityBadge.classList.add('badge-sold');
                        addToOrderBtn.disabled = true;
                    } else if (week.status === 'low_stock') {
                        availabilityBadge.classList.add('badge-low');
                        addToOrderBtn.disabled = false;
                    } else {
                        availabilityBadge.classList.add('badge-available');
                        addToOrderBtn.disabled = false;
                    }
                } else {
                    weekAvailabilityInfo.style.display = 'none';
                    addToOrderBtn.disabled = true;
                }
            }

            // Validate if Add to Order button should be enabled
            function validateAddToOrder(weekId, weeksMap) {
                const addToOrderBtn = document.getElementById('add-to-order-btn');
                const quantityInput = document.getElementById('quantity-input');
                
                if (!weekId || !weeksMap[weekId]) {
                    addToOrderBtn.disabled = true;
                    return;
                }
                
                const week = weeksMap[weekId];
                const quantity = parseInt(quantityInput.value);
                
                // Check if quantity is valid
                const validQuantity = quantity > 0 && quantity <= week.available;
                
                // Enable/disable Add to Order button
                addToOrderBtn.disabled = !validQuantity || week.status === 'sold_out';
            }

            // Add event listeners for quantity controls
            const decreaseQtyBtn = document.getElementById('decrease-qty');
            const increaseQtyBtn = document.getElementById('increase-qty');
            
            if (decreaseQtyBtn) {
                decreaseQtyBtn.addEventListener('click', function() {
                    const quantityInput = document.getElementById('quantity-input');
                    const currentValue = parseInt(quantityInput.value);
                    if (currentValue > 1) {
                        quantityInput.value = currentValue - 1;
                        const selectedWeekId = document.getElementById('selected-week-id');
                        validateAddToOrder(selectedWeekId.value, weeksMap);
                    }
                });
            }
            
            if (increaseQtyBtn) {
                increaseQtyBtn.addEventListener('click', function() {
                    const quantityInput = document.getElementById('quantity-input');
                    const selectedWeekId = document.getElementById('selected-week-id');
                    const weekId = selectedWeekId.value;
                    
                    if (weekId && weeksMap[weekId]) {
                        const maxAvailable = weeksMap[weekId].available;
                        const currentValue = parseInt(quantityInput.value);
                        if (currentValue < maxAvailable) {
                            quantityInput.value = currentValue + 1;
                        }
                        validateAddToOrder(weekId, weeksMap);
                    }
                });
            }
            
            const quantityInput = document.getElementById('quantity-input');
            if (quantityInput) {
                quantityInput.addEventListener('change', function() {
                    const selectedWeekId = document.getElementById('selected-week-id');
                    const weekId = selectedWeekId.value;
                    
                    if (weekId && weeksMap[weekId]) {
                        const maxAvailable = weeksMap[weekId].available;
                        const currentValue = parseInt(this.value);
                        
                        if (isNaN(currentValue) || currentValue < 1) {
                            this.value = 1;
                        } else if (currentValue > maxAvailable) {
                            this.value = maxAvailable;
                        }
                        validateAddToOrder(weekId, weeksMap);
                    }
                });
            }
        } catch (error) {
            console.error('Error initializing date picker:', error);
        }
    }
    
    // Start the initialization process
    initializeFlatpickr();
});
