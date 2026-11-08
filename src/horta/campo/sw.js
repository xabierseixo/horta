const CACHE_NAME = 'agroxest360-campo-v1';
const RECURSOS_ESTATICOS = [
  '/campo/',
  '/campo/index.html',
  '/campo/app.js',
  '/campo/estilo.css',
  '/campo/manifest.webmanifest',
  '/campo/icona.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(RECURSOS_ESTATICOS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((nomes) => {
      return Promise.all(
        nomes.map((nome) => {
          if (nome !== CACHE_NAME) {
            return caches.delete(nome);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Nunca gardar na caché as chamadas á API nin métodos que non sexan GET
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((respostaCache) => {
      if (respostaCache) {
        return respostaCache;
      }
      return fetch(event.request).then((respostaRede) => {
        if (!respostaRede || respostaRede.status !== 200 || respostaRede.type !== 'basic') {
          return respostaRede;
        }
        const respostaClon = respostaRede.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, respostaClon);
        });
        return respostaRede;
      }).catch(() => {
        if (event.request.mode === 'navigate') {
          return caches.match('/campo/');
        }
      });
    })
  );
});
