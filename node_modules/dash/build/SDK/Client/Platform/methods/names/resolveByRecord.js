"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolveByRecord = void 0;
const wasm_dpp_1 = require("@dashevo/wasm-dpp");
/**
 * @param record - the exact name of the record to resolve
 * @param value - the exact value for this record to resolve
 * @returns {ExtendedDocument[]} - Resolved domains
 */
async function resolveByRecord(record, value) {
    await this.initialize();
    if (record === 'identity') {
        value = wasm_dpp_1.Identifier.from(value);
    }
    return await this.documents.get('dpns.domain', {
        where: [
            [`records.${record}`, '==', value],
        ],
    });
}
exports.resolveByRecord = resolveByRecord;
exports.default = resolveByRecord;
//# sourceMappingURL=resolveByRecord.js.map