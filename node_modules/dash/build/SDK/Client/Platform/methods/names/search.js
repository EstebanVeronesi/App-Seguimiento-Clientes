"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.search = void 0;
const convertToHomographSafeChars_1 = __importDefault(require("../../../../../utils/convertToHomographSafeChars"));
/**
 *
 * @param {string} labelPrefix - label prefix to search for
 * @param {string} parentDomainName - parent domain name on which to perform the search
 * @returns Documents[] - The array of documents that match the search parameters.
 */
async function search(labelPrefix, parentDomainName = '') {
    await this.initialize();
    const normalizedParentDomainName = convertToHomographSafeChars_1.default(parentDomainName);
    const normalizedLabelPrefix = convertToHomographSafeChars_1.default(labelPrefix);
    const documents = await this.documents.get('dpns.domain', {
        where: [
            ['normalizedParentDomainName', '==', normalizedParentDomainName],
            ['normalizedLabel', 'startsWith', normalizedLabelPrefix],
        ],
        orderBy: [
            ['normalizedLabel', 'asc'],
        ],
    });
    return documents;
}
exports.search = search;
exports.default = search;
//# sourceMappingURL=search.js.map