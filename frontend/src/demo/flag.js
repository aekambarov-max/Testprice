// Сборка `vite build --mode demo`: интерфейс работает без сервера, на имитаторе API (src/demo/mockServer.js).
export const DEMO = import.meta.env.MODE === 'demo'
