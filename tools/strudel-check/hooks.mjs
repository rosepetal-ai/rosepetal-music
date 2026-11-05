// @strudel/core 1.2.6 importa SalatRepl de @kabelsalat/web, que necesita el navegador y no carga en Node.
// El verificador no lo usa, así que se resuelve a un módulo vacío. Solo para Node anterior a 22.15 (sin registerHooks).
export async function resolve(specifier, context, nextResolve) {
  if (specifier === '@kabelsalat/web') return { url: new URL('./kabelsalat-vacio.mjs', import.meta.url).href, shortCircuit: true };
  return nextResolve(specifier, context);
}
