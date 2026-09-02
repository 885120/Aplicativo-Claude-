// Doppler Obstétrico — funcionamento offline
// Guarda a página no aparelho na primeira visita com internet.
// Nas visitas seguintes: abre da memória (rápido, funciona sem sinal) e
// atualiza a cópia guardada em segundo plano sempre que houver internet.
var CACHE = 'doppler-v1';

self.addEventListener('install', function (e) {
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (chaves) {
      return Promise.all(
        chaves.filter(function (k) { return k !== CACHE; })
              .map(function (k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;

  e.respondWith(
    caches.open(CACHE).then(function (cache) {
      return cache.match(e.request).then(function (guardado) {
        var rede = fetch(e.request).then(function (resposta) {
          if (resposta && resposta.status === 200) {
            cache.put(e.request, resposta.clone());
          }
          return resposta;
        }).catch(function () {
          return guardado; // sem internet: usa o que já está guardado
        });
        return guardado || rede;
      });
    })
  );
});
