# The Fisherman House

MultiLoader Minecraft mod that adds a beachside **Fisherman House** structure.

## Features

- Custom jigsaw structure (`fisherman_house:fisherman_house`)
- Spawns in beach biomes
- Terrain adaptation (`beard_box`) with structure-block stripping processors
- Fabric, Forge, and NeoForge builds where the version tree supports them

## Project layout

```
the-fisherman-house/
  shared/resources/   # Canonical datapack assets (NBT + worldgen + lang)
  1.20.1/             # Fabric + Forge
  1.21.1/             # Fabric + Forge + NeoForge
  26.1.2/             # Fabric + NeoForge
  26.2/               # Fabric + NeoForge
```

## Supported versions

| Minecraft | Fabric | Forge | NeoForge | JDK |
|-----------|--------|-------|----------|-----|
| 1.20.1    | Yes    | Yes   | —        | 17  |
| 1.21.1    | Yes    | Yes   | Yes      | 21  |
| 26.1.2    | Yes    | —     | Yes      | 25  |
| 26.2      | Yes    | —     | Yes      | 25  |

## Build

```powershell
# 1.20.1 (JDK 17)
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"
cd 1.20.1
.\gradlew.bat build

# 1.21.1 (JDK 21)
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot"
cd ..\1.21.1
.\gradlew.bat build

# 26.1.2 / 26.2 (JDK 25)
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-25.0.4.7-hotspot"
cd ..\26.1.2
.\gradlew.bat build
cd ..\26.2
.\gradlew.bat build
```

Built JARs are written to each loader's `build/libs/` directory.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

See [.github/SECURITY.md](.github/SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
