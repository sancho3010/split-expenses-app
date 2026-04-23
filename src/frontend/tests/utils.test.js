import { formatMoney, formatDate, getGroupEmoji, getExpenseEmoji, groupEmojis } from "../js/utils.js";

// --- formatMoney ---

describe("formatMoney", () => {
    test("formatea un entero sin decimales", () => {
        const result = formatMoney(50000);
        expect(result).toMatch(/50/);
    });

    test("formatea un número con decimales truncándolos", () => {
        const result = formatMoney(1234.567);
        expect(result).toMatch(/1/);
        expect(result).not.toMatch(/567/);
    });

    test("formatea cero", () => {
        expect(formatMoney(0)).toMatch(/0/);
    });

    test("formatea un string numérico", () => {
        const result = formatMoney("75000");
        expect(result).toMatch(/75/);
    });
});

// --- formatDate ---

describe("formatDate", () => {
    test("devuelve día y mes abreviado", () => {
        const result = formatDate("2025-03-15T10:00:00Z");
        expect(result).toMatch(/15/);
    });

    test("maneja formato ISO completo", () => {
        const result = formatDate("2024-12-01T23:59:59.000Z");
        expect(result).toBeDefined();
        expect(typeof result).toBe("string");
    });
});

// --- getGroupEmoji ---

describe("getGroupEmoji", () => {
    test("devuelve un emoji del array predefinido", () => {
        const emoji = getGroupEmoji("Viaje a Cartagena");
        expect(groupEmojis).toContain(emoji);
    });

    test("es determinista: mismo nombre, mismo emoji", () => {
        const first = getGroupEmoji("Arriendo Marzo");
        const second = getGroupEmoji("Arriendo Marzo");
        expect(first).toBe(second);
    });

    test("nombres distintos pueden dar emojis distintos", () => {
        const results = new Set(
            ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"].map(getGroupEmoji)
        );
        expect(results.size).toBeGreaterThanOrEqual(2);
    });

    test("funciona con string vacío", () => {
        const emoji = getGroupEmoji("");
        expect(groupEmojis).toContain(emoji);
    });
});

// --- getExpenseEmoji ---

describe("getExpenseEmoji", () => {
    test.each([
        ["Hotel en Bogotá", "🏨"],
        ["Alojamiento rural", "🏨"],
        ["Comida rápida", "🍽️"],
        ["Almuerzo ejecutivo", "🍽️"],
        ["Cena grupal", "🍽️"],
        ["Uber al aeropuerto", "🚕"],
        ["Taxi centro", "🚕"],
        ["Transporte público", "🚕"],
        ["Cerveza artesanal", "🍻"],
        ["Tragos en el bar", "🍻"],
        ["Bar nocturno", "🍻"],
        ["Supermercado Éxito", "🛒"],
        ["Mercado campesino", "🛒"],
    ])("'%s' → %s", (desc, expected) => {
        expect(getExpenseEmoji(desc)).toBe(expected);
    });

    test("descripción sin categoría devuelve 💳", () => {
        expect(getExpenseEmoji("Regalo de cumpleaños")).toBe("💳");
        expect(getExpenseEmoji("Entrada al museo")).toBe("💳");
    });

    test("es case-insensitive", () => {
        expect(getExpenseEmoji("HOTEL")).toBe("🏨");
        expect(getExpenseEmoji("Cerveza")).toBe("🍻");
    });
});
