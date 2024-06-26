// Global vars

export const twitch = window.Twitch.ext

const params = new URLSearchParams(window.location.search)
const state = params.get('state')
export let extensionUri = 'https://mulletwebhook.jaedolph.net'

// change EBS URL if testing
if (state === 'testing') {
  extensionUri = 'https://mulletwebhook-test.jaedolph.net'
}
