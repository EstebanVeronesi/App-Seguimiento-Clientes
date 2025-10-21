import { Identifier } from '@dashevo/wasm-dpp';
import { Platform } from '../../Platform';
declare type ContractIdentifier = string | Identifier;
/**
 * Get contracts from the platform
 *
 * @param {ContractIdentifier} identifier - identifier of the contract to fetch
 * @param {bigint} startAtMs
 * @param {number} limit
 * @param {number} offset
 * @returns contracts
 */
export declare function history(this: Platform, identifier: ContractIdentifier, startAtMs: bigint, limit: number, offset: number): Promise<any>;
export default history;
