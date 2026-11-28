# Informe del Gate 3

Fecha: 2026-11-28
Modo: sin Docker
Huella de la evidencia: 4eae57a9507e
Puntaje: 100.0 de 100 (umbral 60)
Nota: 7.0 (escala 1 a 7; 60 puntos dan 4.0)
Resultado: PROVISIONAL

## Criterios

| ID | Criterio | Peso | Puntos | Evidencia |
|----|----------|------|--------|-----------|
| C1 | Problema, requerimientos y arquitectura | 10 | 10.0 | ficha 1/1, decisiones 7/7 |
| C2 | Funcionamiento end-to-end | 25 | 25.0 | frio 5/5, demo 8/8 |
| C3 | Integracion IA, orquestacion y RAG | 15 | 15.0 | mitigaciones 17/17, ia 29/29 |
| C4 | Backend FastAPI y Docker | 15 | 15.0 | servicio 7/7, api_md 1/1, dockerfile 7/7, compose 7/7 |
| C5 | QA, pruebas y evaluacion de calidad | 10 | 10.0 | pytest 255/255, matriz 6/6, parciales 5/5 |
| C6 | Seguridad, riesgos y trazabilidad | 10 | 10.0 | riesgos 6/6, secretos 5/5 |
| C7 | Documentacion tecnica | 5 | 5.0 | readme 8/8, transferencia 6/6 |
| C8 | Demo y defensa tecnica | 10 | 10.0 | guion 9/9, demo 8/8, respaldo 8/8 |

## No compensables

| ID | Criterio | Estado |
|----|----------|--------|
| NC-1 | La solucion se ejecuta de punta a punta en el entorno contenerizado | cumple |
| NC-2 | El servicio expone endpoints funcionales y validados | cumple |
| NC-3 | La demo se ejecuta en vivo sobre la solucion construida, no sobre material grabado | lo confirma el evaluador |
| NC-4 | Sin credenciales ni datos reales en el repositorio ni en el corpus | cumple |

## Lo que confirma el evaluador

| ID | Que confirma |
|----|--------------|
| NC-3 | Que la demostracion corra en vivo, en la defensa. |
| NC-4 | Que los datos del corpus sean simulados. |

## Entregables

| Entregable | Archivos |
|------------|----------|
| Codigo y contenedor | Dockerfile, compose.yaml, servicio/main.py |
| README tecnico | README.md |
| Matrices de prueba y riesgo | docs/matriz_pruebas.md, docs/matriz_riesgos.md |
| Demo en vivo | ensayo_demo.py, docs/demo_respaldo.md |
| Presentacion ejecutiva | docs/defensa.md |

## Lo que este informe no demuestra

- Que la presentacion se haya construido: solo se mide el guion.
- Que el tiempo de la demo sea el de una persona real: es una estimacion con 130 palabras por minuto.
- Que los criterios no compensables sean los definitivos: son una propuesta del equipo de diseno instruccional que el validador debe confirmar.
- Lo que solo confirma el evaluador (ver la seccion anterior).
- Lo que viva en los contenedores, si el modo fue sin Docker.
