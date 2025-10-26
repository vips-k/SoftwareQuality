package com.example.softwareQuality.automation;

import java.util.HashMap;
import java.util.Map;

public class TestContext {
    private final Map<String, Object> data = new HashMap<>();

    public void put(String key, Object value) {
        data.put(key, value);
    }

    @SuppressWarnings("unchecked")
    public <T> T get(String key, Class<T> clazz) {
        Object val = data.get(key);
        if (val == null) return null;
        return (T) val;
    }

    public boolean contains(String key) {
        return data.containsKey(key);
    }
}

