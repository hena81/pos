// Add item to cart
function addToCart(product) {
    const productId = product.id;
    const productName = product.name;
    const productPrice = product.price;
    
    // Check if product already in cart
    const existingItem = cart.find(item => item.product_id === productId);
    
    if (existingItem) {
        // Increase quantity
        existingItem.quantity += 1;
        existingItem.total = existingItem.quantity * existingItem.price;
        updateCartItemUI(productId, existingItem.quantity, existingItem.total);
    } else {
        // Add new item
        const newItem = {
            product_id: productId,
            name: productName,
            price: productPrice,
            quantity: 1,
            total: productPrice
        };
        
        cart.push(newItem);
        
        // Add item to cart UI
        $('#empty-cart-message').hide();
        $('#cart-items').append(`
            <div class="cart-item cart-item-enter" id="cart-item-${productId}">
                <button class="remove-item" data-id="${productId}">
                    <i class="fas fa-times"></i>
                </button>
                <div class="cart-item-header">
                    <span class="cart-item-name">${productName}</span>
                </div>
                <div class="cart-item-controls">
                    <div class="quantity-control">
                        <button class="quantity-btn decrease-qty" data-id="${productId}">-</button>
                        <input type="text" class="quantity-input" value="1" readonly>
                        <button class="quantity-btn increase-qty" data-id="${productId}">+</button>
                    </div>
                    <div class="product-price-display">
                        <span class="item-total">${productPrice.toFixed(2)}</span> دينار
                    </div>
                </div>
                <div class="price-calculation">${1} × ${productPrice.toFixed(2)} دينار</div>
            </div>
        `);
    }
    
    updateCartTotal();
}

// Update cart item UI
// Update cart item UI with improved styling
function updateCartItemUI(productId, quantity, total) {
    const $item = $(`#cart-item-${productId}`);
    const price = total / quantity;
    
    // Update quantity display
    $item.find('.quantity-input').val(quantity);
    
    // Update price displays
    $item.find('.item-price-value').text(total.toFixed(2));
    $item.find('.price-calculation').html(`${quantity} × ${price.toFixed(2)} دينار`);
    
    // Add highlight effect
    $item.addClass('highlight');
    setTimeout(() => {
        $item.removeClass('highlight');
    }, 300);
}

// Add item to cart with improved UI
function addToCart(product) {
    const productId = product.id;
    const productName = product.name;
    const productPrice = product.price;
    
    // Check if product already in cart
    const existingItem = cart.find(item => item.product_id === productId);
    
    if (existingItem) {
        // Increase quantity
        existingItem.quantity += 1;
        existingItem.total = existingItem.quantity * existingItem.price;
        updateCartItemUI(productId, existingItem.quantity, existingItem.total);
    } else {
        // Add new item
        const newItem = {
            product_id: productId,
            name: productName,
            price: productPrice,
            quantity: 1,
            total: productPrice
        };
        
        cart.push(newItem);
        
        // Add item to cart UI
        $('#empty-cart-message').hide();
        $('#cart-items').append(`
            <div class="cart-item" id="cart-item-${productId}">
                <div class="cart-item-header">
                    <span class="cart-item-name">${productName}</span>
                    <button class="btn-remove-item remove-item" data-id="${productId}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="cart-item-details">
                    <div class="quantity-control">
                        <button class="btn-quantity decrease-qty" data-id="${productId}">-</button>
                        <span class="item-quantity">1</span>
                        <button class="btn-quantity increase-qty" data-id="${productId}">+</button>
                    </div>
                    <span class="item-total">${productPrice.toFixed(3)} د.ك</span>
                </div>
            </div>
        `);
    }
    
    // Update cart total
    function updateCartTotal() {
        const total = cart.reduce((sum, item) => sum + item.total, 0);
        $('#cart-total').text(total.toFixed(3) + ' د.ك');
        
        // Enable/disable buttons based on cart state
        if (cart.length > 0) {
            $('#checkout-btn, #clear-cart-btn').prop('disabled', false);
        } else {
            $('#checkout-btn, #clear-cart-btn').prop('disabled', true);
        }
    }
}