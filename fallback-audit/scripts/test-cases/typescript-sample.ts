// F003: null masking with ?? 
function getDisplayName(user: User | null): string {
    return user?.displayName ?? "Anonymous";
}

function getTimeout(config: Config | null): number {
    return config?.timeout ?? 5000;
}

// F004: fallback chain
function getEmail(user: User | null): string {
    return user?.email ?? user?.username ?? "unknown@example.com";
}

// F001: catch with return default
async function fetchData(url: string): Promise<Data> {
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (e) {
        return { items: [] };
    }
}

// F002: silent catch
function process(value: string): void {
    try {
        riskyOperation(value);
    } catch (e) {
    }
}
