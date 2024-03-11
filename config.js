'use strict'
import { twitch, extensionUri } from './globals.js'

let authorization

twitch.onAuthorized(function (auth) {
  authorization = 'Bearer ' + auth.token
  console.log('bits enabled: ' + twitch.features.isBitsEnabled)
})


// add the auth token to the request as a header
htmx.on("htmx:configRequest", (e)=> {
  e.detail.headers["Authorization"] = authorization
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
      const cancelButton = document.getElementById("cancel-button")
      dialog.showModal()
      dialog.addEventListener("close", () => {
        dialog.remove()
      })
      cancelButton.addEventListener("click", () => {
        dialog.close()
      })
  }
})

htmx.on('closeModal', function() {
  console.log("closing modal dialog")
  document.querySelector('dialog[open]').close();
});


document.body.addEventListener("htmx:afterRequest", (event) => {
  console.log("event")
  console.log(event.detail.xhr)
})

// twitch.onAuthorized(function (auth) {
//   authorization = 'Bearer ' + auth.token
//   getLayoutList().then((layoutList) => {
//     console.log(layoutList)
//     for (const layout of layoutList.layouts) {
//         const newOption = document.createElement('option')
//         console.log(layout)
//         newOption.value = layout.id
//         newOption.text = layout.name
//         document.getElementById('layout_select').appendChild(newOption)
//     }
//   }).catch(function (error) {
//     console.error(error)
//   })
// })

// async function getLayoutList () {
//     const layoutsUrl = extensionUri + '/layouts'

//     // get list of a channel's layouts using the EBS
//     const response = await fetch(layoutsUrl, {
//         method: 'GET',
//         headers: {
//         'Content-Type': 'application/json',
//         Authorization: authorization
//         }
//     })

//     if (!response.ok) {
//         return await response.text().then(text => {
//         const errorMessage = 'could not get layouts: ' + response.status + ' ' + text
//         throw new Error(errorMessage)
//         })
//     }

//     const layouts = await response.json()
//     return layouts
// }
