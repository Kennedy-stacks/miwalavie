document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("checkout-btn");

  button.addEventListener("click", () => {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];

    if (cart.length === 0) {
      alert("Your cart is empty!");
      return;
    }

    // create WhatsApp message
    let message = "Hello! I'd like to order the following items:\n\n";

    cart.forEach((item, index) => {
      message += `${index + 1}. ${item.name} - ${item.quantity} x ${item.price}\n`;
    });

    message += "\nPlease confirm availability. Thank you!";

    // encode message for URL
    const encodedMessage = encodeURIComponent(message);
    const waLink = `https://wa.me/2347061724876?text=${encodedMessage}`;

    // redirect
    window.location.href = waLink;
  });
});
