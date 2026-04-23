export default {
    testMatch: ["<rootDir>/tests/**/*.test.js"],
    collectCoverageFrom: [
        "js/utils.js",
    ],
    coverageDirectory: "coverage",
    coverageReporters: ["lcov", "text"],
    reporters: [
        "default",
        ["jest-html-reporter", {
            outputPath: "ci_frontend_unit_report.html",
            pageTitle: "Frontend Unit Tests",
        }],
    ],
    transform: {},
};
