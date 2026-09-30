// Doppler Obstétrico — service worker clínico endurecido
// Release do worker: R14.21-SW2
//
// Objetivos de segurança operacional:
// - ONLINE: a navegação clínica usa a resposta atual da rede, nunca cache-first.
// - OFFLINE REAL: usa somente uma cópia previamente validada do próprio app.
// - NÃO APAGA o último fallback antigo até confirmar uma cópia válida no cache novo.
// - Só gerencia navegações HTML do próprio escopo; outros GETs não são cacheados.
// - Query strings não são cacheadas/interceptadas para evitar ambiguidade e dados sensíveis.
// - Respostas 4xx/5xx ou HTML estranho nunca contaminam o cache clínico.

var SW_VERSION = 'R14.21-SW2';
var CACHE_PREFIX = 'doppler-clinical-';
var CACHE = 'doppler-clinical-r14.21-sw2';
var LEGACY_CACHES = ['doppler-v1'];

// Assinaturas estáveis do HTML clínico. Servem para impedir que uma página 200
// de login, portal cativo, erro customizado ou outro HTML seja guardada/servida offline.
var APP_MARKERS = [
  '<title>Doppler Obstétrico</title>',
  'APP_VERSAO',
  'id="sintRes"'
];

function warn(msg, err) {
  try {
    if (self.console && self.console.warn) self.console.warn('[Doppler SW ' + SW_VERSION + '] ' + msg, err || '');
  } catch (_) {}
}

function isOwnedCacheName(name) {
  return name.indexOf(CACHE_PREFIX) === 0 || LEGACY_CACHES.indexOf(name) !== -1;
}

function sameOriginAndScope(url) {
  try {
    var u = new URL(url);
    var scope = new URL(self.registration.scope);
    return u.origin === scope.origin && u.href.indexOf(scope.href) === 0;
  } catch (_) {
    return false;
  }
}

// Mantemos a query como parte da identidade. Porém, por segurança, navegações com
// query string não são interceptadas nem armazenadas (ver isManagedNavigation()).
function navigationKey(url) {
  var u = new URL(url);
  u.hash = '';
  return u.href;
}

function isManagedNavigation(request) {
  if (!request || request.method !== 'GET' || request.mode !== 'navigate') return false;
  if (!sameOriginAndScope(request.url)) return false;

  // Fail closed: hoje o app não usa querystring. Se isso mudar no futuro, a política
  // deve ser revista conscientemente em vez de misturar URLs potencialmente diferentes
  // ou armazenar parâmetros com dados sensíveis no CacheStorage.
  try {
    if (new URL(request.url).search) return false;
  } catch (_) {
    return false;
  }
  return true;
}

function responseCanBeClinicalHtml(response) {
  if (!response || response.status !== 200 || response.type === 'opaque') return false;

  // Redirecionamentos para fora do escopo nunca podem virar fallback clínico.
  if (response.url && !sameOriginAndScope(response.url)) return false;

  var ct = '';
  try { ct = response.headers.get('Content-Type') || ''; } catch (_) {}
  if (ct && ct.toLowerCase().indexOf('text/html') === -1 &&
            ct.toLowerCase().indexOf('application/xhtml+xml') === -1) return false;

  return true;
}

function validateClinicalHtmlSnapshot(response) {
  if (!responseCanBeClinicalHtml(response)) return Promise.resolve(false);

  // Esta função CONSOME a resposta recebida. Passe sempre um clone quando precisar
  // preservar a resposta original para navegador ou CacheStorage.
  return response.text().then(function (html) {
    for (var i = 0; i < APP_MARKERS.length; i++) {
      if (html.indexOf(APP_MARKERS[i]) === -1) return false;
    }
    return true;
  }).catch(function () {
    return false;
  });
}

function validateClinicalHtmlResponse(response) {
  if (!responseCanBeClinicalHtml(response)) return Promise.resolve(false);
  var copy;
  try { copy = response.clone(); }
  catch (_) { return Promise.resolve(false); }
  return validateClinicalHtmlSnapshot(copy);
}

function deleteOldOwnedCaches() {
  return caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (key) {
      return isOwnedCacheName(key) && key !== CACHE;
    }).map(function (key) {
      return caches.delete(key).catch(function (err) {
        warn('Falha ao remover cache antigo ' + key, err);
        return false;
      });
    }));
  }).catch(function (err) {
    warn('Falha ao listar caches antigos', err);
    return [];
  });
}

function storeValidatedResponse(key, response) {
  if (!responseCanBeClinicalHtml(response)) return Promise.resolve(false);

  // Captura as duas cópias ANTES de a resposta original ser entregue ao navegador.
  // Isso elimina corrida entre consumo do body e response.clone().
  var validationCopy, cacheCopy;
  try {
    validationCopy = response.clone();
    cacheCopy = response.clone();
  } catch (_) {
    return Promise.resolve(false);
  }

  return validateClinicalHtmlSnapshot(validationCopy).then(function (valid) {
    if (!valid) return false;
    return caches.open(CACHE).then(function (cache) {
      return cache.put(key, cacheCopy).then(function () { return true; });
    });
  }).catch(function (err) {
    warn('Não foi possível atualizar o fallback offline', err);
    return false;
  });
}

// Procura primeiro no cache atual e depois nos caches antigos deste MESMO app.
// Cada resposta é revalidada antes de ser usada, inclusive o legado doppler-v1.
function findValidCachedNavigation(key) {
  return caches.keys().then(function (keys) {
    var names = [];
    if (keys.indexOf(CACHE) !== -1) names.push(CACHE);

    // CacheStorage mantém ordem de criação; percorremos os antigos do mais recente
    // para o mais antigo. Caches de outras aplicações nunca entram nesta lista.
    var old = keys.filter(function (name) {
      return name !== CACHE && isOwnedCacheName(name);
    }).reverse();
    names = names.concat(old);

    function next(index) {
      if (index >= names.length) return Promise.resolve(null);
      return caches.open(names[index]).then(function (cache) {
        return cache.match(key);
      }).then(function (response) {
        if (!response) return next(index + 1);
        return validateClinicalHtmlResponse(response).then(function (valid) {
          return valid ? response : next(index + 1);
        });
      }).catch(function () {
        return next(index + 1);
      });
    }

    return next(0);
  }).catch(function () {
    return null;
  });
}

// Depois do registro/ativação, tenta preparar offline as páginas clínicas que já
// estão abertas. Se estiver sem internet, NÃO apaga o cache antigo: preserva o último
// fallback conhecido até uma atualização online bem-sucedida.
function prepareOpenClinicalClients() {
  return self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
    var urls = [];
    var seen = {};

    clientList.forEach(function (client) {
      if (!client || !client.url || !sameOriginAndScope(client.url)) return;
      var u;
      try { u = new URL(client.url); } catch (_) { return; }
      if (u.search) return;
      var key = navigationKey(u.href);
      if (!seen[key]) {
        seen[key] = true;
        urls.push(key);
      }
    });

    if (!urls.length) return 0;

    return Promise.all(urls.map(function (url) {
      return fetch(url, {
        cache: 'no-store',
        credentials: 'same-origin',
        redirect: 'follow'
      }).then(function (response) {
        return storeValidatedResponse(url, response);
      }).catch(function () {
        return false;
      });
    })).then(function (results) {
      var ok = 0;
      results.forEach(function (v) { if (v) ok++; });
      return ok;
    });
  }).catch(function (err) {
    warn('Não foi possível preparar clientes abertos para offline', err);
    return 0;
  });
}

self.addEventListener('install', function (event) {
  // O novo worker não fica esperando o antigo encerrar. A Promise é ligada ao evento
  // para tornar a transição explícita no lifecycle.
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    self.clients.claim().then(function () {
      return prepareOpenClinicalClients();
    }).then(function (preparedCount) {
      // Só aposentamos o cache anterior depois de existir ao menos uma cópia válida
      // no cache novo. Offline durante upgrade => cache legado é preservado.
      if (preparedCount > 0) return deleteOldOwnedCaches();
      return null;
    }).catch(function (err) {
      // Uma falha de cache não deve impedir o worker de atuar como network-first.
      warn('Ativação concluída com modo offline degradado', err);
      return null;
    })
  );
});

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (!isManagedNavigation(request)) return;

  var key = navigationKey(request.url);

  // Uma única ida à rede. Antes de expor a resposta ao navegador, o wrapper captura
  // clones suficientes para validação/cache, evitando corrida de bodyUsed.
  var preparedNetwork = fetch(request, { cache: 'no-store' }).then(function (response) {
    var validationCopy = null;
    var cacheCopy = null;

    if (responseCanBeClinicalHtml(response)) {
      try {
        validationCopy = response.clone();
        cacheCopy = response.clone();
      } catch (_) {
        validationCopy = null;
        cacheCopy = null;
      }
    }

    return {
      response: response,
      validationCopy: validationCopy,
      cacheCopy: cacheCopy
    };
  });

  // Atualiza o fallback em paralelo e mantém o worker vivo até a gravação terminar.
  // A navegação online não espera CacheStorage para exibir a resposta atual da rede.
  var updateTask = preparedNetwork.then(function (packet) {
    if (!packet.validationCopy || !packet.cacheCopy) return false;

    return validateClinicalHtmlSnapshot(packet.validationCopy).then(function (valid) {
      if (!valid) return false;
      return caches.open(CACHE).then(function (cache) {
        return cache.put(key, packet.cacheCopy).then(function () { return true; });
      });
    }).then(function (stored) {
      // Só depois de persistir uma nova cópia válida removemos versões anteriores.
      if (stored) return deleteOldOwnedCaches().then(function () { return true; });
      return false;
    }).catch(function (err) {
      warn('Atualização do cache em background falhou', err);
      return false;
    });
  }).catch(function () {
    return false;
  });

  event.waitUntil(updateTask);

  event.respondWith(
    preparedNetwork.then(function (packet) {
      // Rede respondeu: devolvemos exatamente o que veio do servidor.
      // 4xx/5xx e HTML 200 inválido NÃO são substituídos silenciosamente por cache antigo.
      return packet.response;
    }).catch(function () {
      // Somente falha real de rede entra no modo offline.
      return findValidCachedNavigation(key).then(function (cached) {
        if (cached) return cached;
        return new Response(
          'Aplicativo indisponível offline. Abra esta versão ao menos uma vez com internet para preparar o modo offline.',
          {
            status: 503,
            headers: {
              'Content-Type': 'text/plain; charset=utf-8',
              'Cache-Control': 'no-store'
            }
          }
        );
      });
    })
  );
});
