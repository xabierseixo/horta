/**
 * AgroXest360 Campo — PWA sen cobertura.
 * JavaScript sinxelo sen compilación nin librarías externas.
 */

(function () {
  'use strict';

  // Chaves de almacenamento
  const CLAVE_STORAGE_TOKEN = 'campo_token';
  const CLAVE_STORAGE_HORTA_ID = 'campo_horta_id';
  const CLAVE_STORAGE_HORTA_NOME = 'campo_horta_nome';

  // Base de datos IndexedDB
  const DB_NOME = 'agroxest360_campo_db';
  const DB_VERSION = 1;
  const TÁBOA_DATOS = 'datos_mestres';
  const TÁBOA_COLA = 'cola_rexistros';

  // Estado da aplicación en memoria
  let db = null;
  let datosMestresActuais = null;
  let hortaIdActiva = null;
  let hortaNomeActiva = null;

  // --- IndexedDB ---

  function abrirDB() {
    return new Promise((resolve, reject) => {
      if (db) {
        resolve(db);
        return;
      }
      const peticion = indexedDB.open(DB_NOME, DB_VERSION);

      peticion.onupgradeneeded = (evento) => {
        const base = evento.target.result;
        if (!base.objectStoreNames.contains(TÁBOA_DATOS)) {
          base.createObjectStore(TÁBOA_DATOS, { keyPath: 'horta_id' });
        }
        if (!base.objectStoreNames.contains(TÁBOA_COLA)) {
          const colaStore = base.createObjectStore(TÁBOA_COLA, { keyPath: 'uuid' });
          colaStore.createIndex('horta_id', 'horta_id', { unique: false });
          colaStore.createIndex('estado', 'estado', { unique: false });
        }
      };

      peticion.onsuccess = (evento) => {
        db = evento.target.result;
        resolve(db);
      };

      peticion.onerror = (evento) => {
        reject(evento.target.error);
      };
    });
  }

  async function gardarDatosMestresDB(hortaId, datos) {
    const base = await abrirDB();
    return new Promise((resolve, reject) => {
      const trans = base.transaction([TÁBOA_DATOS], 'readwrite');
      const store = trans.objectStore(TÁBOA_DATOS);
      const rexistro = {
        horta_id: Number(hortaId),
        datos: datos,
        data_descarga: new Date().toISOString()
      };
      const peticion = store.put(rexistro);
      peticion.onsuccess = () => resolve(rexistro);
      peticion.onerror = () => reject(peticion.error);
    });
  }

  async function obterDatosMestresDB(hortaId) {
    const base = await abrirDB();
    return new Promise((resolve, reject) => {
      const trans = base.transaction([TÁBOA_DATOS], 'readonly');
      const store = trans.objectStore(TÁBOA_DATOS);
      const peticion = store.get(Number(hortaId));
      peticion.onsuccess = () => resolve(peticion.result || null);
      peticion.onerror = () => reject(peticion.error);
    });
  }

  async function engadirRexistroColaDB(rexistro) {
    const base = await abrirDB();
    return new Promise((resolve, reject) => {
      const trans = base.transaction([TÁBOA_COLA], 'readwrite');
      const store = trans.objectStore(TÁBOA_COLA);
      const peticion = store.put(rexistro);
      peticion.onsuccess = () => resolve(rexistro);
      peticion.onerror = () => reject(peticion.error);
    });
  }

  async function listarColaDB(hortaId) {
    const base = await abrirDB();
    return new Promise((resolve, reject) => {
      const trans = base.transaction([TÁBOA_COLA], 'readonly');
      const store = trans.objectStore(TÁBOA_COLA);
      const peticion = store.getAll();
      peticion.onsuccess = () => {
        const todos = peticion.result || [];
        const filtrados = todos.filter((r) => Number(r.horta_id) === Number(hortaId));
        resolve(filtrados);
      };
      peticion.onerror = () => reject(peticion.error);
    });
  }

  async function borrarRexistroColaDB(uuid) {
    const base = await abrirDB();
    return new Promise((resolve, reject) => {
      const trans = base.transaction([TÁBOA_COLA], 'readwrite');
      const store = trans.objectStore(TÁBOA_COLA);
      const peticion = store.delete(uuid);
      peticion.onsuccess = () => resolve(true);
      peticion.onerror = () => reject(peticion.error);
    });
  }

  // --- Utilidades ---

  function obterToken() {
    return localStorage.getItem(CLAVE_STORAGE_TOKEN) || '';
  }

  function gardarToken(token) {
    localStorage.setItem(CLAVE_STORAGE_TOKEN, token.trim());
  }

  function limparToken() {
    localStorage.removeItem(CLAVE_STORAGE_TOKEN);
  }

  function dataHoxeISO() {
    const d = new Date();
    const ano = d.getFullYear();
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const dia = String(d.getDate()).padStart(2, '0');
    return `${ano}-${mes}-${dia}`;
  }

  function formatarDataHoraGalego(isoString) {
    if (!isoString) return 'Descoñecida';
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return isoString;
      const dia = String(d.getDate()).padStart(2, '0');
      const mes = String(d.getMonth() + 1).padStart(2, '0');
      const hora = String(d.getHours()).padStart(2, '0');
      const min = String(d.getMinutes()).padStart(2, '0');
      return `${dia}/${mes} ${hora}:${min}`;
    } catch {
      return isoString;
    }
  }

  function mostrarAviso(texto, tipo = 'info', duracionSeg = 5) {
    const contedor = document.getElementById('contedor-avisos');
    if (!contedor) return;

    const div = document.createElement('div');
    div.className = `aviso aviso-${tipo}`;

    const span = document.createElement('span');
    span.textContent = texto;
    div.appendChild(span);

    const btnPechar = document.createElement('button');
    btnPechar.type = 'button';
    btnPechar.className = 'btn-pechar-aviso';
    btnPechar.innerHTML = '&times;';
    btnPechar.onclick = () => div.remove();
    div.appendChild(btnPechar);

    contedor.appendChild(div);

    if (duracionSeg > 0) {
      setTimeout(() => {
        if (div.parentNode) div.remove();
      }, duracionSeg * 1000);
    }
  }

  function mostrarVista(nomeVista) {
    const vistas = [
      'vista-conexion',
      'vista-explotacions',
      'vista-principal',
      'vista-formulario',
      'vista-tarefas',
      'vista-cola'
    ];
    vistas.forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        if (id === `vista-${nomeVista}`) {
          el.classList.remove('oculta');
        } else {
          el.classList.add('oculta');
        }
      }
    });

    const barraExplotacion = document.getElementById('barra-explotacion');
    const barraSincro = document.getElementById('barra-sincronizacion');

    if (nomeVista === 'conexion' || nomeVista === 'explotacions') {
      if (barraExplotacion) barraExplotacion.classList.add('oculta');
      if (barraSincro) barraSincro.classList.add('oculta');
    } else {
      if (barraExplotacion) barraExplotacion.classList.remove('oculta');
      if (barraSincro) barraSincro.classList.remove('oculta');
    }
  }

  // --- Indicador de Cobertura ---

  function actualizarEstadoRede() {
    const indicador = document.getElementById('indicador-rede');
    const texto = document.getElementById('texto-indicador-rede');
    if (!indicador || !texto) return;

    if (navigator.onLine) {
      indicador.className = 'indicador-cobertura con';
      texto.textContent = 'Con cobertura';
    } else {
      indicador.className = 'indicador-cobertura sen';
      texto.textContent = 'Sen cobertura';
    }
  }

  // --- Conexión e Explotacións ---

  async function comprobarClaveNoHash() {
    const hash = window.location.hash;
    if (hash && hash.includes('clave=')) {
      const match = hash.match(/clave=([^&]+)/);
      if (match && match[1]) {
        const clave = decodeURIComponent(match[1]).trim();
        if (clave) {
          gardarToken(clave);
          history.replaceState(null, '', window.location.pathname + window.location.search);
        }
      }
    }
  }

  async function descargarExplotacions() {
    const token = obterToken();
    if (!token) {
      mostrarVista('conexion');
      return;
    }

    if (!navigator.onLine) {
      // Se estamos sen rede pero xa temos explotación seleccionada, imos á principal
      if (hortaIdActiva) {
        await cargarExplotacion(hortaIdActiva, hortaNomeActiva);
        return;
      }
      mostrarAviso('Sen cobertura para conectar por primeira vez.', 'erro', 7);
      return;
    }

    try {
      const resposta = await fetch('/api/campo/explotacions', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (resposta.status === 401) {
        limparToken();
        mostrarAviso('A clave de dispositivo non é válida ou foi revogada.', 'erro', 7);
        mostrarVista('conexion');
        return;
      }

      if (!resposta.ok) {
        throw new Error(`Erro ${resposta.status}`);
      }

      const lista = await resposta.json();
      if (!Array.isArray(lista) || lista.length === 0) {
        mostrarAviso('Non tes acceso a ningunha explotación con este dispositivo.', 'erro', 7);
        mostrarVista('conexion');
        return;
      }

      // Se xa tiñamos unha escollida e segue na lista
      const atopada = lista.find((h) => Number(h.id) === Number(hortaIdActiva));
      if (atopada) {
        await cargarExplotacion(atopada.id, atopada.nome);
        return;
      }

      // Se só hai unha, escollemos automaticamente
      if (lista.length === 1) {
        await cargarExplotacion(lista[0].id, lista[0].nome);
        return;
      }

      // Mostramos o selector de explotacións
      mostrarSelectorExplotacions(lista);
    } catch (erro) {
      mostrarAviso(`Non se puido conectar: ${erro.message}`, 'erro', 5);
      if (hortaIdActiva) {
        await cargarExplotacion(hortaIdActiva, hortaNomeActiva);
      } else {
        mostrarVista('conexion');
      }
    }
  }

  function mostrarSelectorExplotacions(lista) {
    const contedor = document.getElementById('lista-explotacions');
    if (!contedor) return;
    contedor.innerHTML = '';

    lista.forEach((exp) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-secundario item-explotacion';
      btn.innerHTML = `<strong>${exp.nome}</strong><span class="etiqueta-pequena">Rol: ${exp.rol}</span>`;
      btn.onclick = () => cargarExplotacion(exp.id, exp.nome);
      contedor.appendChild(btn);
    });

    mostrarVista('explotacions');
  }

  async function cargarExplotacion(id, nome) {
    hortaIdActiva = Number(id);
    hortaNomeActiva = nome || `Explotación #${id}`;
    localStorage.setItem(CLAVE_STORAGE_HORTA_ID, String(hortaIdActiva));
    localStorage.setItem(CLAVE_STORAGE_HORTA_NOME, hortaNomeActiva);

    const elNome = document.getElementById('nome-explotacion-activa');
    if (elNome) elNome.textContent = hortaNomeActiva;

    // Recuperar datos mestres gardados en IndexedDB
    const rexistroGuardado = await obterDatosMestresDB(hortaIdActiva);
    if (rexistroGuardado && rexistroGuardado.datos) {
      datosMestresActuais = rexistroGuardado.datos;
      actualizarEtiquetaDataDatos(rexistroGuardado.data_descarga);
    } else {
      actualizarEtiquetaDataDatos(null);
    }

    mostrarVista('principal');
    await actualizarContaCola();

    // Se temos rede, actualizamos datos se non os tiñamos ou para estar ao día
    if (navigator.onLine) {
      if (!datosMestresActuais) {
        await actualizarDatosMestresServidor();
      }
      await sincronizarCola(true);
    }
  }

  function actualizarEtiquetaDataDatos(dataDescarga) {
    const el = document.getElementById('texto-data-datos');
    if (!el) return;
    if (dataDescarga) {
      el.textContent = `Datos do ${formatarDataHoraGalego(dataDescarga)}`;
    } else {
      el.textContent = 'Sen datos descargados';
    }
  }

  async function actualizarDatosMestresServidor() {
    if (!hortaIdActiva) return;
    if (!navigator.onLine) {
      mostrarAviso('Non hai cobertura para actualizar os datos agora.', 'info', 4);
      return;
    }

    const token = obterToken();
    try {
      const resposta = await fetch(`/api/campo/explotacions/${hortaIdActiva}/datos`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (resposta.status === 401) {
        limparToken();
        mostrarAviso('A sesión do dispositivo caducou.', 'erro', 5);
        mostrarVista('conexion');
        return;
      }

      if (!resposta.ok) {
        throw new Error(`Erro ${resposta.status}`);
      }

      const datos = await resposta.json();
      datosMestresActuais = datos;
      const gardado = await gardarDatosMestresDB(hortaIdActiva, datos);
      actualizarEtiquetaDataDatos(gardado.data_descarga);
      mostrarAviso('Datos da explotación actualizados.', 'ok', 3);
    } catch (e) {
      mostrarAviso(`Erro ao actualizar datos: ${e.message}`, 'erro', 4);
    }
  }

  // --- Conta da Cola de Pendentes ---

  async function actualizarContaCola() {
    if (!hortaIdActiva) return;
    const items = await listarColaDB(hortaIdActiva);
    const pendentes = items.filter((i) => i.estado === 'pendente' || i.estado === 'erro');
    const elConta = document.getElementById('conta-pendentes');
    if (elConta) elConta.textContent = String(pendentes.length);
  }

  // --- Formularios de Apuntar ---

  function prepararFormularioComun() {
    const inputData = document.getElementById('campo-data');
    if (inputData) inputData.value = dataHoxeISO();

    const selectPersoa = document.getElementById('campo-persoa');
    if (selectPersoa) {
      selectPersoa.innerHTML = '<option value="">(Selecciona unha persoa)</option>';
      if (datosMestresActuais && Array.isArray(datosMestresActuais.persoas)) {
        datosMestresActuais.persoas.forEach((p) => {
          const opt = document.createElement('option');
          opt.value = p.id;
          opt.textContent = p.nome;
          selectPersoa.appendChild(opt);
        });
      }
    }

    const campoNotas = document.getElementById('campo-notas');
    if (campoNotas) campoNotas.value = '';
  }

  function abrirFormulario(tipo) {
    if (!datosMestresActuais) {
      mostrarAviso('Non hai datos da explotación dispoñibles. Conéctate para descargalos.', 'erro', 5);
      return;
    }

    prepararFormularioComun();

    const inputTipo = document.getElementById('form-tipo-rexistro');
    if (inputTipo) inputTipo.value = tipo;

    const tituloEl = document.getElementById('titulo-formulario');
    const camposDinamicos = document.getElementById('campos-dinamicos');
    if (!camposDinamicos) return;
    camposDinamicos.innerHTML = '';

    if (tipo === 'observacion') {
      if (tituloEl) tituloEl.textContent = 'Observación de praga';
      construirCamposObservacion(camposDinamicos);
    } else if (tipo === 'rega') {
      if (tituloEl) tituloEl.textContent = 'Apuntar rega';
      construirCamposRega(camposDinamicos);
    } else if (tipo === 'labor') {
      if (tituloEl) tituloEl.textContent = 'Apuntar labor';
      construirCamposLabor(camposDinamicos);
    } else if (tipo === 'colleita') {
      if (tituloEl) tituloEl.textContent = 'Apuntar colleita';
      construirCamposColleita(camposDinamicos);
    }

    mostrarVista('formulario');
  }

  // 1. Observación de praga
  function construirCamposObservacion(contedor) {
    const cultivos = datosMestresActuais.cultivos || [];
    const pragasPorCultivo = datosMestresActuais.pragas_por_cultivo || {};
    const metodos = datosMestresActuais.metodos || {};
    const unidadesConto = datosMestresActuais.unidades_conto || {};
    const niveis = datosMestresActuais.niveis || {};

    // Cultivo
    const grupoCultivo = document.createElement('div');
    grupoCultivo.className = 'campo-grupo';
    grupoCultivo.innerHTML = `
      <label for="obs-cultivo" class="etiqueta">Cultivo *</label>
      <select id="obs-cultivo" class="input-select" required>
        <option value="">(Selecciona un cultivo)</option>
        ${cultivos.map((c) => `<option value="${c.id}">${c.nome}</option>`).join('')}
      </select>
    `;
    contedor.appendChild(grupoCultivo);

    // Problema (Praga, enfermidade ou mala herba)
    const grupoProblema = document.createElement('div');
    grupoProblema.className = 'campo-grupo';
    grupoProblema.innerHTML = `
      <label for="obs-problema" class="etiqueta">Problema (praga / enfermidade) *</label>
      <select id="obs-problema" class="input-select" required>
        <option value="">(Primeiro selecciona un cultivo)</option>
      </select>
    `;
    contedor.appendChild(grupoProblema);

    const selectCultivo = grupoCultivo.querySelector('#obs-cultivo');
    const selectProblema = grupoProblema.querySelector('#obs-problema');

    selectCultivo.addEventListener('change', () => {
      const cId = selectCultivo.value;
      selectProblema.innerHTML = '<option value="">(Selecciona un problema)</option>';
      if (!cId || !pragasPorCultivo[cId]) {
        return;
      }
      const problemasCultivo = pragasPorCultivo[cId];
      const categorias = [
        { chave: 'praga', nome: 'Pragas' },
        { chave: 'enfermidade', nome: 'Enfermidades' },
        { chave: 'mala_herba', nome: 'Malas herbas' }
      ];

      categorias.forEach((cat) => {
        const mapa = problemasCultivo[cat.chave];
        if (mapa && Object.keys(mapa).length > 0) {
          const optgroup = document.createElement('optgroup');
          optgroup.label = cat.nome;
          Object.entries(mapa).forEach(([cod, desc]) => {
            const opt = document.createElement('option');
            opt.value = `${cat.chave}:${cod}`;
            opt.textContent = desc;
            optgroup.appendChild(opt);
          });
          selectProblema.appendChild(optgroup);
        }
      });
    });

    // Método
    const grupoMetodo = document.createElement('div');
    grupoMetodo.className = 'campo-grupo';
    grupoMetodo.innerHTML = `
      <label for="obs-metodo" class="etiqueta">Método *</label>
      <select id="obs-metodo" class="input-select" required>
        ${Object.entries(metodos)
          .map(([k, v]) => `<option value="${k}">${v}</option>`)
          .join('')}
      </select>
    `;
    contedor.appendChild(grupoMetodo);

    // Reconto e Unidade
    const filaConto = document.createElement('div');
    filaConto.className = 'fila-campos';
    filaConto.innerHTML = `
      <div class="campo-grupo">
        <label for="obs-conto" class="etiqueta">Reconto numérico</label>
        <input id="obs-conto" type="number" step="any" class="input-texto" placeholder="Ex: 5">
      </div>
      <div class="campo-grupo">
        <label for="obs-unidade-conto" class="etiqueta">Unidade de reconto</label>
        <select id="obs-unidade-conto" class="input-select">
          <option value="">(Ningunha)</option>
          ${Object.entries(unidadesConto)
            .map(([k, v]) => `<option value="${k}">${v}</option>`)
            .join('')}
        </select>
      </div>
    `;
    contedor.appendChild(filaConto);

    // Nivel cualitativo
    const grupoNivel = document.createElement('div');
    grupoNivel.className = 'campo-grupo';
    grupoNivel.innerHTML = `
      <label for="obs-nivel" class="etiqueta">Nivel cualitativo</label>
      <select id="obs-nivel" class="input-select">
        <option value="">(Non indicado)</option>
        ${Object.entries(niveis)
          .map(([k, v]) => `<option value="${k}">${v}</option>`)
          .join('')}
      </select>
    `;
    contedor.appendChild(grupoNivel);
  }

  // 2. Rega
  function construirCamposRega(contedor) {
    const cultivos = datosMestresActuais.cultivos || [];
    const sistemasRega = datosMestresActuais.sistemas_rega || {};

    // Cultivo
    const grupoCultivo = document.createElement('div');
    grupoCultivo.className = 'campo-grupo';
    grupoCultivo.innerHTML = `
      <label for="rega-cultivo" class="etiqueta">Cultivo</label>
      <select id="rega-cultivo" class="input-select">
        <option value="">(Toda a leira / xeral)</option>
        ${cultivos.map((c) => `<option value="${c.id}">${c.nome}</option>`).join('')}
      </select>
    `;
    contedor.appendChild(grupoCultivo);

    // Cantidade e Unidade (Litros "4" ou m³ "3")
    const filaAuga = document.createElement('div');
    filaAuga.className = 'fila-campos';
    filaAuga.innerHTML = `
      <div class="campo-grupo">
        <label for="rega-cantidade" class="etiqueta">Cantidade de auga</label>
        <input id="rega-cantidade" type="number" step="any" class="input-texto" placeholder="Ex: 500">
      </div>
      <div class="campo-grupo">
        <label for="rega-unidade" class="etiqueta">Unidade</label>
        <select id="rega-unidade" class="input-select">
          <option value="4" selected>Litros (L)</option>
          <option value="3">Metros cúbicos (m³)</option>
        </select>
      </div>
    `;
    contedor.appendChild(filaAuga);

    // Sistema de rega
    const grupoSistema = document.createElement('div');
    grupoSistema.className = 'campo-grupo';
    grupoSistema.innerHTML = `
      <label for="rega-sistema" class="etiqueta">Sistema de rega</label>
      <select id="rega-sistema" class="input-select">
        <option value="">(Selecciona o sistema)</option>
        ${Object.entries(sistemasRega)
          .map(([k, v]) => `<option value="${k}">${v}</option>`)
          .join('')}
      </select>
    `;
    contedor.appendChild(grupoSistema);
  }

  // 3. Labor
  function construirCamposLabor(contedor) {
    const cultivos = datosMestresActuais.cultivos || [];
    const tiposLabor = datosMestresActuais.tipos_labor || {};
    const maquinas = datosMestresActuais.maquinas || [];

    // Tipo de labor
    const grupoTipo = document.createElement('div');
    grupoTipo.className = 'campo-grupo';
    grupoTipo.innerHTML = `
      <label for="labor-tipo" class="etiqueta">Tipo de labor *</label>
      <select id="labor-tipo" class="input-select" required>
        <option value="">(Selecciona o labor)</option>
        ${Object.entries(tiposLabor)
          .map(([k, v]) => `<option value="${k}">${v}</option>`)
          .join('')}
      </select>
    `;
    contedor.appendChild(grupoTipo);

    // Cultivo
    const grupoCultivo = document.createElement('div');
    grupoCultivo.className = 'campo-grupo';
    grupoCultivo.innerHTML = `
      <label for="labor-cultivo" class="etiqueta">Cultivo</label>
      <select id="labor-cultivo" class="input-select">
        <option value="">(Ningún / xeral)</option>
        ${cultivos.map((c) => `<option value="${c.id}">${c.nome}</option>`).join('')}
      </select>
    `;
    contedor.appendChild(grupoCultivo);

    // Máquina
    const grupoMaquina = document.createElement('div');
    grupoMaquina.className = 'campo-grupo';
    grupoMaquina.innerHTML = `
      <label for="labor-maquina" class="etiqueta">Máquina</label>
      <select id="labor-maquina" class="input-select">
        <option value="">(Sen máquina)</option>
        ${maquinas.map((m) => `<option value="${m.id}">${m.alias}</option>`).join('')}
      </select>
    `;
    contedor.appendChild(grupoMaquina);
  }

  // 4. Colleita
  function construirCamposColleita(contedor) {
    const cultivos = datosMestresActuais.cultivos || [];

    // Cultivo
    const grupoCultivo = document.createElement('div');
    grupoCultivo.className = 'campo-grupo';
    grupoCultivo.innerHTML = `
      <label for="colleita-cultivo" class="etiqueta">Cultivo colleitado *</label>
      <select id="colleita-cultivo" class="input-select" required>
        <option value="">(Selecciona o cultivo)</option>
        ${cultivos.map((c) => `<option value="${c.id}">${c.nome}</option>`).join('')}
      </select>
    `;
    contedor.appendChild(grupoCultivo);

    // Cantidade e Unidade
    const filaCantidade = document.createElement('div');
    filaCantidade.className = 'fila-campos';
    filaCantidade.innerHTML = `
      <div class="campo-grupo">
        <label for="colleita-cantidade" class="etiqueta">Cantidade *</label>
        <input id="colleita-cantidade" type="number" step="any" min="0.01" class="input-texto" placeholder="Ex: 120" required>
      </div>
      <div class="campo-grupo">
        <label for="colleita-unidade" class="etiqueta">Unidade *</label>
        <input id="colleita-unidade" type="text" class="input-texto" value="kg" placeholder="kg, caixas..." required>
      </div>
    `;
    contedor.appendChild(filaCantidade);

    // Lote
    const grupoLote = document.createElement('div');
    grupoLote.className = 'campo-grupo';
    grupoLote.innerHTML = `
      <label for="colleita-lote" class="etiqueta">Lote (opcional)</label>
      <input id="colleita-lote" type="text" class="input-texto" placeholder="Identificador de lote">
    `;
    contedor.appendChild(grupoLote);
  }

  // --- Gardar Formulario ---

  async function procesarEnvioFormulario(evento) {
    evento.preventDefault();

    const tipo = document.getElementById('form-tipo-rexistro').value;
    const dataVal = document.getElementById('campo-data').value;
    const persoaVal = document.getElementById('campo-persoa').value;
    const notasVal = document.getElementById('campo-notas').value.trim();

    if (!dataVal) {
      mostrarAviso('Indica a data do traballo.', 'erro', 4);
      return;
    }

    const persoaId = persoaVal ? Number(persoaVal) : null;
    let datosRexistro = {};

    if (tipo === 'observacion') {
      const cultivoVal = document.getElementById('obs-cultivo').value;
      const problemaVal = document.getElementById('obs-problema').value;
      const metodoVal = document.getElementById('obs-metodo').value;
      const contoVal = document.getElementById('obs-conto').value;
      const unidadeContoVal = document.getElementById('obs-unidade-conto').value;
      const nivelVal = document.getElementById('obs-nivel').value;

      if (!cultivoVal) {
        mostrarAviso('Debes escoller un cultivo para a observación.', 'erro', 4);
        return;
      }
      if (!problemaVal) {
        mostrarAviso('Debes escoller un problema da lista.', 'erro', 4);
        return;
      }
      const partesProblema = problemaVal.split(':');
      const problemaTipo = partesProblema[0];
      const problemaCodigo = partesProblema[1];

      datosRexistro = {
        cultivo_id: Number(cultivoVal),
        data: dataVal,
        problema_tipo: problemaTipo,
        problema_codigo: problemaCodigo,
        metodo: metodoVal || 'sintomas',
        conto: contoVal ? parseFloat(contoVal) : null,
        unidade_conto: unidadeContoVal || null,
        nivel: nivelVal || null,
        notas: notasVal || null,
        persoa_id: persoaId
      };
    } else if (tipo === 'rega') {
      const cultivoVal = document.getElementById('rega-cultivo').value;
      const cantidadeVal = document.getElementById('rega-cantidade').value;
      const unidadeVal = document.getElementById('rega-unidade').value;
      const sistemaVal = document.getElementById('rega-sistema').value;

      datosRexistro = {
        data_inicio: dataVal,
        cultivo_id: cultivoVal ? Number(cultivoVal) : null,
        cantidade: cantidadeVal ? parseFloat(cantidadeVal) : null,
        unidade: unidadeVal || '4',
        sistema_rega: sistemaVal || null,
        notas: notasVal || null,
        persoa_id: persoaId
      };
    } else if (tipo === 'labor') {
      const tipoLaborVal = document.getElementById('labor-tipo').value;
      const cultivoVal = document.getElementById('labor-cultivo').value;
      const maquinaVal = document.getElementById('labor-maquina').value;

      if (!tipoLaborVal) {
        mostrarAviso('Debes escoller o tipo de labor.', 'erro', 4);
        return;
      }

      datosRexistro = {
        data_inicio: dataVal,
        tipo_labor: tipoLaborVal,
        cultivo_id: cultivoVal ? Number(cultivoVal) : null,
        maquina_id: maquinaVal ? Number(maquinaVal) : null,
        notas: notasVal || null,
        persoa_id: persoaId
      };
    } else if (tipo === 'colleita') {
      const cultivoVal = document.getElementById('colleita-cultivo').value;
      const cantidadeVal = document.getElementById('colleita-cantidade').value;
      const unidadeVal = document.getElementById('colleita-unidade').value.trim();
      const loteVal = document.getElementById('colleita-lote').value.trim();

      if (!cultivoVal) {
        mostrarAviso('Debes escoller un cultivo para a colleita.', 'erro', 4);
        return;
      }
      if (!cantidadeVal || parseFloat(cantidadeVal) <= 0) {
        mostrarAviso('Indica unha cantidade colleitada maior ca 0.', 'erro', 4);
        return;
      }
      if (!unidadeVal) {
        mostrarAviso('Indica a unidade de medida da colleita (ex: kg).', 'erro', 4);
        return;
      }

      datosRexistro = {
        cultivo_id: Number(cultivoVal),
        data: dataVal,
        cantidade: parseFloat(cantidadeVal),
        unidade: unidadeVal,
        lote: loteVal || null,
        notas: notasVal || null,
        persoa_id: persoaId
      };
    }

    const novoUuid = crypto.randomUUID();
    const rexistro = {
      uuid: novoUuid,
      horta_id: hortaIdActiva,
      tipo: tipo,
      datos: datosRexistro,
      creado_en: new Date().toISOString(),
      estado: 'pendente',
      erro_mensaxe: null
    };

    await engadirRexistroColaDB(rexistro);
    mostrarAviso('Traballo gardado no móbil.', 'ok', 3);
    await actualizarContaCola();
    mostrarVista('principal');

    if (navigator.onLine) {
      sincronizarCola(true);
    }
  }

  // --- Vista Tarefas Pendentes ---

  async function abrirVistaTarefas() {
    if (!datosMestresActuais) {
      mostrarAviso('Non hai datos da explotación dispoñibles.', 'erro', 4);
      return;
    }

    const contedor = document.getElementById('lista-tarefas-pendentes');
    if (!contedor) return;
    contedor.innerHTML = '';

    const tarefas = datosMestresActuais.tarefas_pendentes || [];
    const cola = await listarColaDB(hortaIdActiva);
    const idsFeitosNaCola = new Set(
      cola
        .filter((r) => r.tipo === 'tarefa_feita')
        .map((r) => Number(r.datos.id))
    );

    const pendentes = tarefas.filter((t) => !idsFeitosNaCola.has(Number(t.id)));

    if (pendentes.length === 0) {
      contedor.innerHTML = '<p class="texto-suave">Non hai tarefas pendentes nesta explotación.</p>';
      mostrarVista('tarefas');
      return;
    }

    pendentes.forEach((t) => {
      const card = document.createElement('div');
      card.className = 'item-tarefa';

      const dataTxt = t.data ? `Para o ${t.data}` : 'Sen data fixada';
      card.innerHTML = `
        <div class="item-tarefa-fila-superior">
          <strong class="item-tarefa-titulo">${t.descricion}</strong>
          <span class="item-tarefa-data">${dataTxt}</span>
        </div>
        <div class="item-tarefa-pe">
          <button type="button" class="btn btn-primario btn-pequeno">Marcar como feita</button>
        </div>
      `;

      card.querySelector('button').onclick = () => completarTarefa(t);
      contedor.appendChild(card);
    });

    mostrarVista('tarefas');
  }

  async function completarTarefa(tarefa) {
    const dataHoxe = dataHoxeISO();
    const persoaDefecto =
      datosMestresActuais && datosMestresActuais.persoas && datosMestresActuais.persoas[0]
        ? datosMestresActuais.persoas[0].id
        : null;

    const novoUuid = crypto.randomUUID();
    const rexistro = {
      uuid: novoUuid,
      horta_id: hortaIdActiva,
      tipo: 'tarefa_feita',
      datos: {
        id: Number(tarefa.id),
        data: dataHoxe,
        persoa_id: persoaDefecto,
        horas: null
      },
      creado_en: new Date().toISOString(),
      estado: 'pendente',
      erro_mensaxe: null
    };

    await engadirRexistroColaDB(rexistro);
    mostrarAviso(`Tarefa «${tarefa.descricion}» completada e gardada no móbil.`, 'ok', 3);
    await actualizarContaCola();
    abrirVistaTarefas();

    if (navigator.onLine) {
      sincronizarCola(true);
    }
  }

  // --- Vista Cola de Pendentes ---

  async function abrirVistaCola() {
    const contedor = document.getElementById('lista-cola-rexistros');
    if (!contedor) return;
    contedor.innerHTML = '';

    const items = await listarColaDB(hortaIdActiva);

    if (items.length === 0) {
      contedor.innerHTML = '<p class="texto-suave">Non hai traballos pendentes por enviar.</p>';
      mostrarVista('cola');
      return;
    }

    const nomesTipos = {
      observacion: 'Observación de praga',
      rega: 'Rega',
      labor: 'Labor',
      colleita: 'Colleita',
      tarefa_feita: 'Tarefa feita'
    };

    items.forEach((item) => {
      const div = document.createElement('div');
      div.className = 'item-cola';

      let resumo = '';
      const d = item.datos || {};
      if (item.tipo === 'observacion') {
        resumo = `Data: ${d.data} · Problema: ${d.problema_tipo || ''}`;
      } else if (item.tipo === 'rega') {
        resumo = `Data: ${d.data_inicio} · Cantidade: ${d.cantidade || '—'} ${d.unidade === '3' ? 'm³' : 'L'}`;
      } else if (item.tipo === 'labor') {
        resumo = `Data: ${d.data_inicio} · Tipo: ${d.tipo_labor}`;
      } else if (item.tipo === 'colleita') {
        resumo = `Data: ${d.data} · Cantidade: ${d.cantidade} ${d.unidade}`;
      } else if (item.tipo === 'tarefa_feita') {
        resumo = `Tarefa ID: ${d.id} · Data: ${d.data}`;
      }

      let erroHtml = '';
      if (item.estado === 'erro') {
        erroHtml = `<div class="item-cola-erro">Erro: ${item.erro_mensaxe || 'Fallou o envío'}</div>`;
      }

      div.innerHTML = `
        <div class="item-cola-fila-superior">
          <strong class="item-cola-titulo">${nomesTipos[item.tipo] || item.tipo}</strong>
          <span class="item-cola-data">${formatarDataHoraGalego(item.creado_en)}</span>
        </div>
        <div class="item-cola-detalles">${resumo}</div>
        ${erroHtml}
        <div class="item-cola-pe">
          <button type="button" class="btn btn-perigo btn-pequeno">Borrar</button>
        </div>
      `;

      div.querySelector('button').onclick = async () => {
        if (confirm('Queres borrar este traballo pendente antes de enviar?')) {
          await borrarRexistroColaDB(item.uuid);
          await actualizarContaCola();
          abrirVistaCola();
        }
      };

      contedor.appendChild(div);
    });

    mostrarVista('cola');
  }

  // --- Envío de Rexistros á API ---

  async function sincronizarCola(silencioso = false) {
    if (!hortaIdActiva) return;

    if (!navigator.onLine) {
      if (!silencioso) {
        mostrarAviso('Sen cobertura para enviar traballos agora.', 'info', 4);
      }
      return;
    }

    const items = await listarColaDB(hortaIdActiva);
    const pendentes = items.filter((r) => r.estado === 'pendente' || r.estado === 'erro');

    if (pendentes.length === 0) {
      if (!silencioso) {
        mostrarAviso('Non hai traballos pendentes por enviar.', 'info', 3);
      }
      return;
    }

    const token = obterToken();
    const corpo = pendentes.map((r) => ({
      uuid: r.uuid,
      tipo: r.tipo,
      datos: r.datos
    }));

    try {
      const resposta = await fetch(`/api/campo/explotacions/${hortaIdActiva}/rexistros`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(corpo)
      });

      if (resposta.status === 401) {
        limparToken();
        mostrarAviso('A clave de dispositivo foi revogada.', 'erro', 5);
        mostrarVista('conexion');
        return;
      }

      if (!resposta.ok) {
        throw new Error(`Erro no servidor (${resposta.status})`);
      }

      const resultados = await resposta.json();
      let enviadosConta = 0;
      let errosConta = 0;

      for (const res of resultados) {
        if (res.estado === 'creado' || res.estado === 'xa_estaba') {
          await borrarRexistroColaDB(res.uuid);
          enviadosConta++;
        } else if (res.estado === 'erro') {
          const itemOriginal = pendentes.find((p) => p.uuid === res.uuid);
          if (itemOriginal) {
            itemOriginal.estado = 'erro';
            itemOriginal.erro_mensaxe = res.mensaxe || 'Erro ao gardar na app principal';
            await engadirRexistroColaDB(itemOriginal);
          }
          errosConta++;
        }
      }

      await actualizarContaCola();

      if (enviadosConta > 0) {
        mostrarAviso(`Enviados ${enviadosConta}`, 'ok', 4);
      }

      if (errosConta > 0) {
        mostrarAviso(`Quedaron ${errosConta} rexistro(s) con erros na cola.`, 'erro', 6);
      }

      // Se estabamos vendo a cola, refrescala
      const vistaCola = document.getElementById('vista-cola');
      if (vistaCola && !vistaCola.classList.contains('oculta')) {
        abrirVistaCola();
      }
    } catch (e) {
      if (!silencioso) {
        mostrarAviso(`Erro ao enviar traballos: ${e.message}`, 'erro', 5);
      }
    }
  }

  // --- Inicialización ---

  function rexistrarServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/campo/sw.js').catch((erro) => {
        console.warn('Erro ao rexistrar o service worker:', erro);
      });
    }
  }

  function vincularEventos() {
    window.addEventListener('online', () => {
      actualizarEstadoRede();
      sincronizarCola(true);
    });

    window.addEventListener('offline', () => {
      actualizarEstadoRede();
    });

    // Conexión
    const btnConectar = document.getElementById('btn-conectar-dispositivo');
    const inputClave = document.getElementById('input-clave');
    if (btnConectar && inputClave) {
      btnConectar.onclick = () => {
        const val = inputClave.value.trim();
        if (!val) {
          mostrarAviso('Por favor, introduce a clave do dispositivo.', 'erro', 3);
          return;
        }
        gardarToken(val);
        inputClave.value = '';
        descargarExplotacions();
      };
    }

    // Cambiar explotación
    const btnCambiarExp = document.getElementById('btn-cambiar-explotacion');
    if (btnCambiarExp) {
      btnCambiarExp.onclick = () => descargarExplotacions();
    }

    // Actualizar datos mestres
    const btnActDatos = document.getElementById('btn-actualizar-datos');
    if (btnActDatos) {
      btnActDatos.onclick = () => actualizarDatosMestresServidor();
    }

    // Cola de traballos
    const btnVerCola = document.getElementById('btn-ver-cola');
    if (btnVerCola) btnVerCola.onclick = () => abrirVistaCola();

    const btnVoltarCola = document.getElementById('btn-voltar-cola');
    if (btnVoltarCola) btnVoltarCola.onclick = () => mostrarVista('principal');

    const btnEnviarCola = document.getElementById('btn-enviar-cola');
    if (btnEnviarCola) btnEnviarCola.onclick = () => sincronizarCola(false);

    const btnEnviarColaVista = document.getElementById('btn-enviar-cola-vista');
    if (btnEnviarColaVista) btnEnviarColaVista.onclick = () => sincronizarCola(false);

    // Botóns de accións principais
    const botonsAccion = document.querySelectorAll('.btn-accion');
    botonsAccion.forEach((btn) => {
      btn.onclick = () => {
        const tipo = btn.getAttribute('data-tipo');
        if (tipo === 'tarefas') {
          abrirVistaTarefas();
        } else {
          abrirFormulario(tipo);
        }
      };
    });

    // Formulario
    const btnCancelarForm = document.getElementById('btn-cancelar-formulario');
    if (btnCancelarForm) {
      btnCancelarForm.onclick = () => mostrarVista('principal');
    }

    const formRexistro = document.getElementById('form-rexistro');
    if (formRexistro) {
      formRexistro.onsubmit = procesarEnvioFormulario;
    }

    // Tarefas pendentes
    const btnVoltarTarefas = document.getElementById('btn-voltar-tarefas');
    if (btnVoltarTarefas) {
      btnVoltarTarefas.onclick = () => mostrarVista('principal');
    }
  }

  async function iniciarApp() {
    rexistrarServiceWorker();
    actualizarEstadoRede();
    vincularEventos();

    hortaIdActiva = Number(localStorage.getItem(CLAVE_STORAGE_HORTA_ID)) || null;
    hortaNomeActiva = localStorage.getItem(CLAVE_STORAGE_HORTA_NOME) || null;

    await comprobarClaveNoHash();

    const token = obterToken();
    if (!token) {
      mostrarVista('conexion');
      return;
    }

    await descargarExplotacions();
  }

  document.addEventListener('DOMContentLoaded', iniciarApp);
})();
