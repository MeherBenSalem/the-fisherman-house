package tn.nightbeam.fishermanhouse.platform;

import java.nio.file.Path;

/** What common code needs from the loader. Each loader passes an implementation to {@code FishermanHouse.init}. */
public interface Platform {
    Path configDir();
}
