package com.skyfx.client.config;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonParseException;

import net.fabricmc.loader.api.FabricLoader;

import com.skyfx.client.SkyFXClient;

/** All SkyFX settings, stored as {@code config/skyfx.json}. */
public final class SkyFXConfig {
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static final Path FILE = FabricLoader.getInstance().getConfigDir().resolve("skyfx.json");
	private static SkyFXConfig instance = new SkyFXConfig();

	// skies
	public String sky = SkyType.AURORA.id();
	/** Animation speed in percent (0 - 300). */
	public int speed = 100;
	/** Sky brightness in percent (50 - 150). */
	public int brightness = 100;
	/** 0 = green, 1 = pink, 2 = blue, 3 = rainbow. */
	public int auroraPalette = 0;
	public boolean hideVanillaClouds = true;
	public boolean matchFog = true;

	// block aura
	public boolean auraEnabled = true;
	public int auraColor = 0x7CF7C5;
	public boolean auraRainbow = false;
	/** Pulse speed in percent (0 = no pulse, up to 300). */
	public int auraPulse = 100;
	/** Glow thickness, 1 - 10. */
	public int auraGlow = 5;
	/** Fill opacity in percent (0 - 60). */
	public int auraFill = 18;

	public static SkyFXConfig get() {
		return instance;
	}

	public SkyType skyType() {
		return SkyType.byId(this.sky);
	}

	public static void load() {
		if (Files.exists(FILE)) {
			try (Reader reader = Files.newBufferedReader(FILE)) {
				SkyFXConfig loaded = GSON.fromJson(reader, SkyFXConfig.class);
				if (loaded != null) {
					instance = loaded;
				}
			} catch (IOException | JsonParseException e) {
				SkyFXClient.LOGGER.warn("Could not read {}, using defaults", FILE, e);
			}
		}
		instance.clamp();
		save();
	}

	public static void save() {
		try {
			Files.createDirectories(FILE.getParent());
			try (Writer writer = Files.newBufferedWriter(FILE)) {
				GSON.toJson(instance, writer);
			}
		} catch (IOException e) {
			SkyFXClient.LOGGER.warn("Could not write {}", FILE, e);
		}
	}

	public static void reset() {
		instance = new SkyFXConfig();
		save();
	}

	private void clamp() {
		this.sky = SkyType.byId(this.sky).id();
		this.speed = Math.clamp(this.speed, 0, 300);
		this.brightness = Math.clamp(this.brightness, 50, 150);
		this.auroraPalette = Math.floorMod(this.auroraPalette, 4);
		this.auraColor &= 0xFFFFFF;
		this.auraPulse = Math.clamp(this.auraPulse, 0, 300);
		this.auraGlow = Math.clamp(this.auraGlow, 1, 10);
		this.auraFill = Math.clamp(this.auraFill, 0, 60);
	}
}
