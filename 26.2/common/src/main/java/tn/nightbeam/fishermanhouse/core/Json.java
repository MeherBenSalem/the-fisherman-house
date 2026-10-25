package tn.nightbeam.fishermanhouse.core;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Small typed readers and builders for config JSON. Readers never throw: a bad value falls back to the default. */
public final class Json {
    private Json() {
    }

    public static JsonObject obj(Object... keyValues) {
        JsonObject object = new JsonObject();
        for (int i = 0; i + 1 < keyValues.length; i += 2) {
            object.add((String) keyValues[i], element(keyValues[i + 1]));
        }
        return object;
    }

    public static JsonArray arr(Object... values) {
        JsonArray array = new JsonArray();
        for (Object value : values) {
            array.add(element(value));
        }
        return array;
    }

    private static JsonElement element(Object value) {
        if (value instanceof JsonElement element) {
            return element;
        }
        if (value instanceof Boolean b) {
            return new JsonPrimitive(b);
        }
        if (value instanceof Number n) {
            return new JsonPrimitive(n);
        }
        return new JsonPrimitive(String.valueOf(value));
    }

    public static JsonElement at(JsonObject root, String path) {
        JsonElement current = root;
        for (String part : path.split("\\.")) {
            if (current == null || !current.isJsonObject()) {
                return null;
            }
            current = current.getAsJsonObject().get(part);
        }
        return current;
    }

    public static JsonObject object(JsonObject root, String path) {
        JsonElement value = at(root, path);
        return value != null && value.isJsonObject() ? value.getAsJsonObject() : new JsonObject();
    }

    public static boolean bool(JsonObject root, String path, boolean fallback) {
        try {
            JsonElement value = at(root, path);
            return value != null && value.isJsonPrimitive() ? value.getAsBoolean() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    public static double num(JsonObject root, String path, double fallback) {
        try {
            JsonElement value = at(root, path);
            return value != null && value.isJsonPrimitive() ? value.getAsDouble() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    public static int integer(JsonObject root, String path, int fallback) {
        return (int) Math.round(num(root, path, fallback));
    }

    public static String str(JsonObject root, String path, String fallback) {
        try {
            JsonElement value = at(root, path);
            return value != null && value.isJsonPrimitive() ? value.getAsString() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    /** A list of strings; a single string is read as a one-element list. */
    public static List<String> strings(JsonObject root, String path) {
        List<String> values = new ArrayList<>();
        JsonElement value = at(root, path);
        if (value == null) {
            return values;
        }
        if (value.isJsonArray()) {
            for (JsonElement element : value.getAsJsonArray()) {
                if (element.isJsonPrimitive()) {
                    values.add(element.getAsString());
                }
            }
        } else if (value.isJsonPrimitive()) {
            values.add(value.getAsString());
        }
        return values;
    }

    /** An object of numbers, e.g. {@code {"minecraft:bone": 1}}. Non-numeric entries are skipped. */
    public static Map<String, Double> numbers(JsonObject root, String path) {
        Map<String, Double> values = new LinkedHashMap<>();
        for (Map.Entry<String, JsonElement> entry : object(root, path).entrySet()) {
            try {
                if (entry.getValue().isJsonPrimitive()) {
                    values.put(entry.getKey(), entry.getValue().getAsDouble());
                }
            } catch (RuntimeException ignored) {
                // Not a number: skip it.
            }
        }
        return values;
    }
}
