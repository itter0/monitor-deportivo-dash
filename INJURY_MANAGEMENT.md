# Gestión de Lesiones - Guía de Uso

## 📋 Descripción General

La nueva funcionalidad permite a los pacientes gestionar sus lesiones directamente desde la sección **"Mis Datos"** y que estas lesiones afecten automáticamente a los ejercicios mostrados en el dashboard principal.

## ✨ Características Principales

### 1. **Ver Lesiones Actuales**
- En la tarjeta "⚕️ GESTIONAR LESIONES" puedes ver todas tus lesiones registradas
- Cada lesión se muestra como un badge rojo con la opción de eliminarla (×)
- Si no hay lesiones, muestra "No hay lesiones registradas"

### 2. **Añadir Nuevas Lesiones**
- Selecciona una lesión del dropdown:
  - 🦵 Rodilla
  - 💪 Codo
  - 🏋️ Hombro
- Haz clic en "➕ AÑADIR"
- El sistema valida que no haya duplicados
- Tu estado de salud cambia automáticamente a "Lesionado"

### 3. **Eliminar Lesiones**
- Haz clic en la "×" de cualquier lesión en el badge
- La lesión se elimina inmediatamente
- Si eliminas todas las lesiones, tu estado vuelve a "Sano"

### 4. **Actualización de Ejercicios (Automática)**
- Cuando añades o eliminas una lesión, **el grid de ejercicios en el Dashboard se actualiza automáticamente**
- Los ejercicios se adaptan a tu(s) lesión(es):
  - **Rodilla**: Ejercicios específicos de rodilla (extensión, flexión, etc.)
  - **Codo**: Ejercicios específicos de codo
  - **Hombro**: Ejercicios específicos de hombro
  - **Sin lesiones**: Ejercicios completos para luchador sano
- El título del grid también se actualiza (ej: "Ejercicios de Rodilla y Codo")

## 🔄 Flujo de Uso

```
1. Inicia sesión como paciente
   ↓
2. Ve a "👤 Mis Datos"
   ↓
3. Busca la tarjeta "⚕️ GESTIONAR LESIONES"
   ↓
4. Añade lesiones O elimina las existentes
   ↓
5. Los cambios se guardan automáticamente
   ↓
6. Vuelve al Dashboard
   ↓
7. Observa los ejercicios actualizados según tus lesiones
```

## 💾 Datos Guardados

Las lesiones y el estado de salud se guardan en:
- **Ubicación**: Base de datos JSON (`rehabidesk_db.json`)
- **Estructura**:
  ```json
  {
    "users": {
      "paciente.torn": {
        "profile": {
          "injury_types": ["rodilla", "codo"],
          "health_status": "lesionado",
          ...
        }
      }
    }
  }
  ```

## 🎯 Mapeo de Lesiones a Ejercicios

| Lesión | Ejercicios | Ejemplos |
|--------|-----------|----------|
| Rodilla | KNEE_EXERCISES | Extensión de Rodilla, Flexión, Sentadillas |
| Codo | ELBOW_EXERCISES | Flexiones de codo, Estiramiento |
| Hombro | SHOULDER_EXERCISES | Rotaciones, Elevaciones |
| Ninguna | HEALTHY_FIGHTER_EXERCISES | Ejercicios completos de combate |

## ⚙️ Validaciones Implementadas

✅ **No permite duplicados**: No puedes añadir la misma lesión dos veces  
✅ **Estado consistente**: Si tienes lesiones, el estado es "lesionado"  
✅ **Limpieza automática**: Si eliminas todas las lesiones, el estado vuelve a "listo"  
✅ **Retroalimentación visual**: Mensajes de éxito/error en tiempo real  

## 🔧 Detalles Técnicos

### Componentes de UI
- **Dropdown**: `add-injury-select` - Selector de lesiones
- **Botón**: `add-injury-btn` - Para añadir lesión
- **Badges**: `injury-badge` - Clickeables para eliminar
- **Grid**: `exercise-grid` - Se actualiza dinámicamente

### Callbacks Implementados
1. **`add_injury()`**: Añade lesión y actualiza UI
2. **`remove_injury()`**: Elimina lesión con un clic
3. **`update_exercises_on_injury_change()`**: Refresca ejercicios dinámicamente

### Base de Datos
- Las lesiones se guardan en `profile['injury_types']` como lista
- El estado en `profile['health_status']`
- Persistencia automática mediante `db.save_user_profile()`

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| La lesión no se guarda | Recarga la página. Verifica que hayas iniciado sesión |
| Los ejercicios no cambian | El grid se actualiza automáticamente. Si no funciona, recarga el dashboard |
| Veo lesiones duplicadas | Limpia el navegador (F5) y vuelve a intentar |
| Error al añadir lesión | Verifica que hayas seleccionado una lesión antes de hacer clic |

## 📝 Notas

- Los cambios se guardan automáticamente en la base de datos
- Solo los pacientes pueden gestionar sus lesiones
- Los médicos ven las lesiones de sus pacientes en la vista de información médica
- Los ejercicios recomendados se actualizan en tiempo real sin recargar la página
