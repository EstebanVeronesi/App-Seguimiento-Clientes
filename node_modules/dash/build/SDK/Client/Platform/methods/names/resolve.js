"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolve = void 0;
const convertToHomographSafeChars_1 = __importDefault(require("../../../../../utils/convertToHomographSafeChars"));
/**
 * This method will allow you to resolve a DPNS record from its humanized name.
 * @param {string} name - the exact alphanumeric (2-63) value used for human-identification
 * @returns {ExtendedDocument} document
 */
async function resolve(name) {
    await this.initialize();
    // setting up variables in case of TLD registration
    let normalizedLabel = name.toLowerCase();
    let normalizedParentDomainName = '';
    // in case of subdomain registration
    // we should split label and parent domain name
    if (name.includes('.')) {
        const normalizedSegments = convertToHomographSafeChars_1.default(name).split('.');
        [normalizedLabel] = normalizedSegments;
        normalizedParentDomainName = normalizedSegments.slice(1).join('.');
    }
    const [document] = await this.documents.get('dpns.domain', {
        where: [
            ['normalizedParentDomainName', '==', normalizedParentDomainName],
            ['normalizedLabel', '==', normalizedLabel],
        ],
    });
    return document === undefined ? null : document;
}
exports.resolve = resolve;
exports.default = resolve;
//# sourceMappingURL=resolve.js.map