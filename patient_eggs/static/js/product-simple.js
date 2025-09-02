// Simple product quantity controls (no weekly selection)
(function(){
  const quantityInput = document.getElementById('quantity');
  if (!quantityInput) return;
  const minQuantity = parseInt(quantityInput.min || '1');
  const maxQuantity = parseInt(quantityInput.max || '100');

  window.increaseSimpleQuantity = function() {
    let currentValue = parseInt(quantityInput.value || '0');
    if (currentValue < maxQuantity) {
      quantityInput.value = currentValue + 1;
    }
  }

  window.decreaseSimpleQuantity = function() {
    let currentValue = parseInt(quantityInput.value || '0');
    if (currentValue > minQuantity) {
      quantityInput.value = currentValue - 1;
    }
  }

  quantityInput.addEventListener('change', function() {
    let value = parseInt(this.value || '0');
    if (isNaN(value) || value < minQuantity) {
      this.value = minQuantity;
    } else if (value > maxQuantity) {
      this.value = maxQuantity;
    }
  });
})();
