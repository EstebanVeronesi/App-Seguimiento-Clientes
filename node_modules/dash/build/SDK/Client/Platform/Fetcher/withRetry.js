"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const fibonacci_1 = require("../../../../utils/fibonacci");
const wait_1 = require("../../../../utils/wait");
/**
 * Maximum number of retry attempts
 */
const withRetry = async (query, maxAttempts, delayMulMs) => {
    let attempt = 0;
    let result;
    if (maxAttempts < 1) {
        throw new Error('maxAttempts must be greater than 0');
    }
    while (attempt < maxAttempts) {
        try {
            result = await query();
            break;
        }
        catch (e) {
            attempt += 1;
            if (attempt >= maxAttempts) {
                throw e;
            }
            const delay = fibonacci_1.fibonacci(attempt) * delayMulMs;
            await wait_1.wait(delay);
        }
    }
    return result;
};
exports.default = withRetry;
//# sourceMappingURL=withRetry.js.map