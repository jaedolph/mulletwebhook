'use strict'
import { twitch, extensionUri } from './globals.js'
/* global htmx:readonly, Sortable:readonly */

let authorization

twitch.onAuthorized(function (auth) {
  authorization = 'Bearer ' + auth.token
  // wait for user to be authorized before getting content for layout-select-form
  htmx.trigger('#layout-select-form', 'authed')
})

// add the auth token to the request as a header
htmx.on('htmx:configRequest', (e) => {
  e.detail.headers.Authorization = authorization

  // update the URL to the proper extension URI
  if (!e.detail.path.startsWith('https')) {
    e.detail.path = extensionUri + e.detail.path
  }
})

htmx.onLoad(function (content) {
  // allow sorting of elements in the panel
  const sortables = content.querySelectorAll('.grid-container')
  for (let i = 0; i < sortables.length; i++) {
    const sortable = sortables[i]
    const sortableInstance = new Sortable(sortable, {
      animation: 150,

      filter: '.add-new-button',
      // disable sorting on the `end` event
      onEnd: function (evt) {
        this.option('disabled', true)
      }
    })

    // re-enable sorting on the `htmx:afterSwap` event
    sortable.addEventListener('htmx:afterSwap', function () {
      sortableInstance.option('disabled', false)
    })
  }
})

htmx.on('htmx:afterSwap', (e) => {
  if (e.detail.target.id === 'dialog') {
    // set up event listeners to close dialog
    const dialog = document.querySelector('dialog')
    const closeButton = document.getElementById('dialog-close-button')
    dialog.showModal()
    dialog.addEventListener('close', () => {
      dialog.remove()
    })
    closeButton.addEventListener('click', () => {
      dialog.close()
    })
  }
})

htmx.on('htmx:beforeSwap', (e) => {
  if (e.detail.target.id === 'dialog-status') {
    if (e.detail.shouldSwap) {
      // workaround to ensure the dialog doesn't close after the webhook is tested
      const closeDialog = (e.detail.serverResponse !== "<p class='success-message'>Webhook OK</p>")

      if (closeDialog) {
        // close the dialog after the success message has been shown for 0.5s
        const dialog = document.querySelector('dialog')
        setTimeout(() => {
          dialog.close()
        }, 500)
      }
    } else {
      // Show the error message on a non-200 response
      e.detail.shouldSwap = true
    }
  }
})
