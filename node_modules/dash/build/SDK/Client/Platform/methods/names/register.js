"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.register = void 0;
const wasm_dpp_1 = require("@dashevo/wasm-dpp");
const convertToHomographSafeChars_1 = __importDefault(require("../../../../../utils/convertToHomographSafeChars"));
const crypto = require('crypto');
const { hash } = require('@dashevo/wasm-dpp/lib/utils/hash');
/**
 * Register names to the platform
 *
 * @param {Platform} this - bound instance class
 * @param {string} name - name
 * @param {Object} records - records object having only one of the following items
 * @param {string} [records.identity]
 * @param identity - identity
 *
 * @returns registered domain document
 */
async function register(name, records, identity) {
    await this.initialize();
    if (records.identity) {
        records.identity = wasm_dpp_1.Identifier.from(records.identity);
    }
    const nameLabels = name.split('.');
    const parentDomainName = nameLabels
        .slice(1)
        .join('.');
    const normalizedParentDomainName = convertToHomographSafeChars_1.default(parentDomainName);
    const [label] = nameLabels;
    const normalizedLabel = convertToHomographSafeChars_1.default(label);
    const preorderSalt = crypto.randomBytes(32);
    const isSecondLevelDomain = normalizedParentDomainName.length > 0;
    const fullDomainName = isSecondLevelDomain
        ? `${normalizedLabel}.${normalizedParentDomainName}`
        : normalizedLabel;
    const saltedDomainHash = hash(Buffer.concat([
        preorderSalt,
        Buffer.from(fullDomainName),
    ]));
    if (!this.client.getApps().has('dpns')) {
        throw new Error('DPNS is required to register a new name.');
    }
    // 1. Create preorder document
    const preorderDocument = await this.documents.create('dpns.preorder', identity, {
        saltedDomainHash,
    });
    await this.documents.broadcast({
        create: [preorderDocument],
    }, identity);
    // 3. Create domain document
    const domainDocument = await this.documents.create('dpns.domain', identity, {
        label,
        normalizedLabel,
        parentDomainName,
        normalizedParentDomainName,
        preorderSalt,
        records,
        subdomainRules: {
            allowSubdomains: !isSecondLevelDomain,
        },
    });
    // 4. Create and send domain state transition
    await this.documents.broadcast({
        create: [domainDocument],
    }, identity);
    return domainDocument;
}
exports.register = register;
exports.default = register;
//# sourceMappingURL=register.js.map