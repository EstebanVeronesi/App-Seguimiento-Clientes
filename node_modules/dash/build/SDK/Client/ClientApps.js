"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClientApps = void 0;
const wasm_dpp_1 = require("@dashevo/wasm-dpp");
class ClientApps {
    constructor(apps = {}) {
        this.apps = {};
        Object.entries(apps).forEach(([name, definition]) => this.set(name, definition));
    }
    /**
       * Set app
       *
       * @param {string} name
       * @param {ClientAppDefinitionOptions} options
       */
    set(name, options) {
        this.apps[name] = {
            contractId: wasm_dpp_1.Identifier.from(options.contractId),
            contract: options.contract,
        };
    }
    /**
       * Get app definition by name
       *
       * @param {string} name
       * @return {ClientAppDefinition}
       */
    get(name) {
        if (!this.has(name)) {
            throw new Error(`Application with name ${name} is not defined`);
        }
        return this.apps[name];
    }
    /**
       * Check if app is defined
       *
       * @param {string} name
       * @return {boolean}
       */
    has(name) {
        return Boolean(this.apps[name]);
    }
    /**
       * Get all apps
       *
       * @return {ClientAppsList}
       */
    getNames() {
        return Object.keys(this.apps);
    }
}
exports.ClientApps = ClientApps;
//# sourceMappingURL=ClientApps.js.map