/**
 * Funciones utilitarias puras.
 * Sin dependencias del DOM ni del backend.
 */

export const groupEmojis = ["🏖️", "🍕", "🏠", "🎉", "✈️", "🎮", "🍻", "⚽", "🎵", "🚗"];

export function formatMoney(amount) {
    return `${Number(amount).toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;
}

export function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString("es-CO", {
        day: "2-digit", month: "short",
    });
}

export function getGroupEmoji(name) {
    let hash = 0;
    for (const ch of name) hash = Math.trunc((hash << 5) - hash + ch.codePointAt(0));
    return groupEmojis[Math.abs(hash) % groupEmojis.length];
}

export function getExpenseEmoji(desc) {
    const d = desc.toLowerCase();
    if (d.includes("hotel") || d.includes("aloj")) return "🏨";
    if (d.includes("comida") || d.includes("almuerzo") || d.includes("cena")) return "🍽️";
    if (d.includes("uber") || d.includes("taxi") || d.includes("transport")) return "🚕";
    if (d.includes("cerveza") || d.includes("trago") || d.includes("bar")) return "🍻";
    if (d.includes("super") || d.includes("mercado")) return "🛒";
    return "💳";
}
