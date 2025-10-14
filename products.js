document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".product-card button");

  buttons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const card = e.target.closest(".product-card");
      const name = card.querySelector("h3").textContent.trim();
      const price = card.querySelector("p").textContent.trim();
      const image = card.querySelector("img").src;
      // prefer data-id, fallback to id attribute
      const id = card.dataset.id || card.id || card.getAttribute("data-id") || null;

      const item = { id, name, price, image, quantity: 1 };

      let cart = JSON.parse(localStorage.getItem("cart")) || [];

      // Check if item already exists by BOTH name and id
      const existing = cart.find((i) => i.name === name && i.id == id);
      if (existing) {
        existing.quantity++;
      } else {
        cart.push(item);
      }

      localStorage.setItem("cart", JSON.stringify(cart));
      alert(`${name} added to your cart!`);
    });
  });
});