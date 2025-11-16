export * from './gAFApi';
import * as http from 'http';

export class HttpError extends Error {
    constructor (public response: http.IncomingMessage, public body: any, public statusCode?: number) {
        super('HTTP request failed');
        this.name = 'HttpError';
    }
}

export { RequestFile } from '../model/models';

// Lazy-load GAFApi to avoid circular dependency
// Import is deferred until APIS is actually accessed
let _APIS: any[] | null = null;
function getAPISInternal() {
    if (!_APIS) {
        // Use require to break circular dependency at module initialization time
        const { GAFApi } = require('./gAFApi');
        _APIS = [GAFApi];
    }
    return _APIS;
}

// Export APIS as a getter for backward compatibility
export const APIS = new Proxy([], {
    get(target, prop) {
        const apis = getAPISInternal();
        const value = (apis as any)[prop];
        if (typeof value === 'function') {
            return value.bind(apis);
        }
        return value;
    },
    has(target, prop) {
        const apis = getAPISInternal();
        return prop in apis;
    },
    ownKeys(target) {
        const apis = getAPISInternal();
        return Object.keys(apis);
    },
    getOwnPropertyDescriptor(target, prop) {
        const apis = getAPISInternal();
        return Object.getOwnPropertyDescriptor(apis, prop);
    }
}) as any;
