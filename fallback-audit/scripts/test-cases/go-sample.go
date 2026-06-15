// F002: ignoring error return with _
package main

func loadConfig() string {
	data, _ := readFile("config.json")
	return data
}

// F005: returning nil result and nil error on failure
func findUser(id string) (*User, error) {
	user, err := db.FindUser(id)
	if err != nil {
		return nil, nil
	}
	return user, nil
}

// F005: direct nil/nil return (extreme null-masking)
func getConfig(key string) (string, error) {
	return nil, nil
}

// F012: silent recover without re-panic
func processItem(item string) {
	defer func() {
		if r := recover(); r != nil {
			_ = r
		}
	}()
	riskyOp(item)
}

// Legitimate: proper error handling
func lookup(id string) (*User, error) {
	user, err := db.FindUser(id)
	if err != nil {
		return nil, fmt.Errorf("lookup failed: %w", err)
	}
	return user, nil
}
