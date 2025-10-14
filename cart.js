document.addEventListener("DOMContentLoaded", () => {
  const cartContainer = document.querySelector(".cart-container");
  const subtotalEl = document.querySelector(".cart-summary p span");

  // get cart from localStorage or empty
  let cart = JSON.parse(localStorage.getItem("cart")) || [];

  // utility functions
  const parsePrice = (text) => {
    if (!text) return 0;
    const num = text.replace(/[^\d.-]/g, "");
    return parseFloat(num) || 0;
  };

  const formatPrice = (value) => {
    return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(value);
  };

  // update subtotal
  const updateSubtotal = () => {
    let total = 0;
    document.querySelectorAll(".cart-item").forEach((item, index) => {
      const priceEl = item.querySelector(".cart-details p");
      const input = item.querySelector(".quantity-control input");
      const price = parsePrice(priceEl?.textContent || "");
      const qty = Math.max(1, Number(input?.value || 1));
      total += price * qty;

      // sync quantity with cart array and localStorage
      cart[index].quantity = qty;
    });

    localStorage.setItem("cart", JSON.stringify(cart));

    if (subtotalEl) subtotalEl.textContent = formatPrice(total);
  };

  // attach item controls
  const attachItemControls = (item, index) => {
    const minus = item.querySelector(".quantity-control button:first-of-type");
    const plus = item.querySelector(".quantity-control button:last-of-type");
    const input = item.querySelector(".quantity-control input");
    const remove = item.querySelector(".remove-btn");

    if (minus) {
      minus.addEventListener("click", () => {
        input.value = Math.max(1, Number(input.value || 1) - 1);
        updateSubtotal();
      });
    }

    if (plus) {
      plus.addEventListener("click", () => {
        input.value = Math.max(1, Number(input.value || 1) + 1);
        updateSubtotal();
      });
    }

    if (input) {
      input.addEventListener("input", () => {
        const v = Math.floor(Number(input.value) || 0);
        input.value = v < 1 ? 1 : v;
        updateSubtotal();
      });
      input.addEventListener("change", updateSubtotal);
    }

    if (remove) {
      remove.addEventListener("click", () => {
        cart.splice(index, 1);
        localStorage.setItem("cart", JSON.stringify(cart));
        renderCart();
      });
    }
  };

  // render cart
  const renderCart = () => {
    cartContainer.innerHTML = "";

    if (cart.length === 0) {
      cartContainer.innerHTML = "<p>Your cart is empty.</p>";
      if (subtotalEl) subtotalEl.textContent = formatPrice(0);
      return;
    }

    cart.forEach((item, index) => {
      const price = parsePrice(item.price);
      const div = document.createElement("div");
      div.classList.add("cart-item");
      div.innerHTML = `
        <img src="${item.image}" alt="${item.name}">
        <div class="cart-details">
          <h3>${item.name}</h3>
          <p>${item.price}</p>
          <div class="quantity-control">
            <button class="decrease">-</button>
            <input type="number" value="${item.quantity}" min="1">
            <button class="increase">+</button>
          </div>
        </div>
        <button class="remove-btn">Remove</button>
      `;
      cartContainer.appendChild(div);
      attachItemControls(div, index);
    });

    updateSubtotal();
  };

  // initial render
  renderCart();

  // observe for dynamically added items (optional)
  if (cartContainer) {
    const obs = new MutationObserver(() => updateSubtotal());
    obs.observe(cartContainer, { childList: true });
  }
});
