  document.getElementById("googleLogin").onclick = () => window.location.href = "/auth/google";

  document.getElementById("facebookLogin").onclick = () => window.location.href = "/auth/facebook";

  document.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      const message = urlParams.get('mensagem');

      if (message) {
          const container = document.querySelector('.container');
          const successDiv = document.createElement('div');
          successDiv.className = 'message success';
          successDiv.textContent = message;
          const h2 = container.querySelector('h2');
          h2.parentNode.insertBefore(successDiv, h2.nextSibling);
      }
  });




    const form = document.querySelector("form");

  form.addEventListener("submit", function (e) {
    const username = form.querySelector("input[name='username']").value;
    const password = form.querySelector("input[name='password']").value;

    if (username === "dev" && password === "dev") {
      e.preventDefault(); // impede envio normal do formulário
      console.log("Login DEV detectado");
      window.location.href = "/login_dev";
    }
  });
function login_usando_senha_dev_e_usuario_dev() {
  window.location.href = "/login_dev";
}


   document.getElementById("googleLogin").addEventListener("click", function () {
      window.location.href = "/auth/google";
    });