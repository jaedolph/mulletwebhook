'use strict'
import { twitch, extensionUri } from './globals.js'

let authorization

twitch.onAuthorized(function (auth) {
  authorization = 'Bearer ' + auth.token
  console.log(auth)
  console.log('bits enabled: ' + twitch.features.isBitsEnabled)
  htmx.trigger("#layout-select-form", "authed")
})

// add the auth token to the request as a header
htmx.on("htmx:configRequest", (e)=> {
  e.detail.headers["Authorization"] = authorization

  // update the URL to the proper extension URI
  if  (!e.detail.path.startsWith("https")) {
    e.detail.path = extensionUri + e.detail.path
  }
})

htmx.onLoad(function(content) {
  console.log("load content")
  var sortables = content.querySelectorAll(".grid-container");
  for (var i = 0; i < sortables.length; i++) {
    var sortable = sortables[i];
    var sortableInstance = new Sortable(sortable, {
      animation: 150,

      filter: ".add-new-button",
      // Disable sorting on the `end` event
      onEnd: function (evt) {
        console.log("sortable enabled")
        this.option("disabled", true);
      }
    });

    // Re-enable sorting on the `htmx:afterSwap` event
    sortable.addEventListener("htmx:afterSwap", function() {
      sortableInstance.option("disabled", false);
      console.log("sortable enabled")
    });
  }
});

htmx.on("htmx:afterSwap", (e) => {
  // Response targeting #dialog => show the modal
  if (e.detail.target.id == "dialog") {
      const dialog = document.querySelector("dialog")
      const closeButton = document.getElementById("dialog-close-button")
      dialog.showModal()
      dialog.addEventListener("close", () => {
        dialog.remove()
      })
      closeButton.addEventListener("click", () => {
        dialog.close()
      })
  }

})

htmx.on("htmx:beforeSwap", (e) => {
  if (e.detail.target.id == "dialog-status") {

      if (e.detail.shouldSwap){
        // workaround to ensure the dialog doesn't close after the webhook is tested
        const close_dialog = (e.detail.serverResponse !== "<p class='success-message'>Webhook OK</p>")

        if (close_dialog) {
          // close the dialog after the success message has been shown for 0.5s
          console.log("closing")
          const dialog = document.querySelector("dialog")
          setTimeout(() => {
            dialog.close()
          }, 500)
        }

      } else {
        console.log(e.detail)
        // Show the error message on a non-200 response
        e.detail.shouldSwap = true
      }
  }

})
