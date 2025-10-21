"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StateTransitionBroadcastError = void 0;
class StateTransitionBroadcastError extends Error {
    /**
       * @param {number} code
       * @param {string} message
       * @param {Error} cause
       */
    constructor(code, message, cause) {
        super(message);
        this.code = code;
        this.message = message;
        this.cause = cause;
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
        Object.setPrototypeOf(this, StateTransitionBroadcastError.prototype);
    }
    /**
       * Returns error code
       *
       * @return {number}
       */
    getCode() {
        return this.code;
    }
    /**
       * Returns error message
       *
       * @return {string}
       */
    getMessage() {
        return this.message;
    }
    /**
       * Get error that was a cause
       *
       * @return {Error}
       */
    getCause() {
        return this.cause;
    }
}
exports.StateTransitionBroadcastError = StateTransitionBroadcastError;
//# sourceMappingURL=StateTransitionBroadcastError.js.map