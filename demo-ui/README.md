# 🐍 HORROCRUXES Demo UI

Interfaz gráfica minimalista para el agente HORROCRUXES de Team Slytherin.

## 🎨 Características

- **Diseño Minimalista** con colores de Harry Potter:
  - Verde/Plateado Slytherin
  - Dorado mágico
  - Fondo oscuro nocturno

- **Funcionalidad:**
  - Input de queries con autocompletado de ejemplos
  - Respuestas con formato Markdown
  - Citaciones resaltadas en dorado
  - Loading state elegante
  - Manejo de errores

## 🚀 Instalación y Uso

### Requisitos Previos
- Node.js >= 18
- Python >= 3.12
- AWS CLI configurado con credenciales del workshop
- Archivo `app/.env` configurado con `AGENT_RUNTIME_ARN`

### Paso 1: Instalar dependencias frontend

```bash
cd demo-ui
npm install
```

### Paso 2: Configurar .env (si no está)

Asegúrate de que `app/.env` tenga:
```env
AWS_REGION=us-east-1
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:XXXXX:runtime/XXXXX
MODEL_ID=us.amazon.nova-lite-v1:0
```

### Paso 3: Iniciar backend API

En una terminal:
```bash
cd demo-ui
python api.py
```

Deberías ver:
```
🐍 Starting HORROCRUXES Demo API on http://localhost:8000
🔗 Agent Runtime: arn:aws:bedrock-agentcore:...
```

### Paso 4: Iniciar frontend React

En OTRA terminal:
```bash
cd demo-ui
npm run dev
```

Deberías ver:
```
  VITE v5.4.11  ready in XXX ms

  ➜  Local:   http://localhost:5173/
```

### Paso 5: Abrir en navegador

Ir a: **http://localhost:5173/**

## 🎮 Uso

1. **Ejemplos Rápidos:** Click en cualquier card de ejemplo para auto-llenar el input
2. **Query Custom:** Escribe tu propia pregunta
3. **Click "Ask CRAFTY":** Envía la query al agente
4. **Ver Respuesta:** Aparecerá abajo con formato bonito y citaciones resaltadas

## 🎨 Colores y Estilo

### Paleta de Colores
- **Slytherin Green:** `#1a472a`, `#2a623d`
- **Slytherin Silver:** `#aaaaaa`, `#7a7a7a`
- **Magic Gold:** `#d4af37`, `#f0c75e`
- **Dark Background:** `#0a0e27`, `#151b3d`
- **Text:** `#f5f5dc` (crema), `#c0c0c0` (gris claro)

### Tipografía
- **Títulos:** Cinzel (serif elegante)
- **Cuerpo:** Lato (sans-serif limpia)

## 📁 Estructura

```
demo-ui/
├── api.py              # Backend FastAPI
├── package.json        # Dependencias Node
├── vite.config.js      # Config Vite
├── index.html          # HTML base
├── src/
│   ├── main.jsx        # Entry point React
│   ├── App.jsx         # Componente principal
│   └── App.css         # Estilos minimalistas HP
└── README.md           # Este archivo
```

## 🐛 Troubleshooting

### Error: "could not read Username for 'https://github.com'"
No afecta la demo, es del repo git. Ignora.

### Error: "Failed to query agent"
- Verifica que `api.py` esté corriendo en puerto 8000
- Verifica AWS credentials: `aws sts get-caller-identity`
- Verifica que `AGENT_RUNTIME_ARN` en `.env` sea correcto

### CORS Error
- Asegúrate de que el frontend corra en puerto 5173
- El backend ya tiene CORS habilitado para ese puerto

### No aparece respuesta
- Abre DevTools (F12) → Console para ver errores
- Verifica que el backend muestre logs de la request

## 🎬 Para la Demo en Vivo

1. **Antes de empezar:** Tener ambos servers corriendo (backend + frontend)
2. **Tener queries listas:** Usa los ejemplos pre-cargados
3. **Internet estable:** Necesitas conexión a AWS
4. **Plan B:** Screenshots de respuestas exitosas como backup

## 🚀 Build para Producción (Opcional)

```bash
npm run build
npm run preview
```

El build estático estará en `dist/` y puede desplegarse en S3, Vercel, etc.

## 📝 Notas

- La UI NO guarda historial local (todo va a AgentCore Memory)
- Session IDs se generan por el backend (AWS AgentCore)
- El agente puede tardar 2-5 segundos en responder (busca en 7 libros)

---

**Desarrollado por Team Slytherin 🐍**
