"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.nearestGreaterFibonacci = exports.fibonacci = void 0;
exports.fibonacci = (n) => {
    if (n < 2) {
        return n;
    }
    return exports.fibonacci(n - 1) + exports.fibonacci(n - 2);
};
exports.nearestGreaterFibonacci = (value) => {
    const phi = (1 + Math.sqrt(5)) / 2;
    // Use the rearranged Binet's formula to find the nearest index
    const n = Math.ceil(Math.log(value * Math.sqrt(5) + 0.5) / Math.log(phi));
    // Calculate the Fibonacci number using Binet's formula
    return Math.round(phi ** n / Math.sqrt(5));
};
//# sourceMappingURL=fibonacci.js.map