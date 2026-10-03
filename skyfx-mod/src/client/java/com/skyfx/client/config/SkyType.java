package com.skyfx.client.config;

import org.jspecify.annotations.Nullable;

/**
 * The selectable skies. Every custom sky is one fragment shader in {@code assets/skyfx/shaders/core/sky_<id>.fsh}.
 * {@code fogColor} is the colour of the sky at the horizon, used to tint the world fog so distant terrain blends in.
 */
public enum SkyType {
	VANILLA("vanilla", null, 0x78A7FF, 0x9FC2FF, 0xC0D8FF),
	AURORA("aurora", new float[] {0.030F, 0.085F, 0.140F}, 0x02060F, 0x0B6E4A, 0x2BE38A),
	GALAXY("galaxy", new float[] {0.030F, 0.020F, 0.070F}, 0x05030C, 0x3A2470, 0xA98BFF),
	ANIME("anime", new float[] {0.720F, 0.890F, 1.000F}, 0x1A57D1, 0x5A9CF5, 0xFFE3D6),
	STORM("storm", new float[] {0.090F, 0.160F, 0.260F}, 0x03060E, 0x1D2D45, 0x9CB6D9);

	private final String id;
	private final float @Nullable [] fogColor;
	private final int[] previewColors;

	SkyType(String id, float @Nullable [] fogColor, int previewTop, int previewMiddle, int previewAccent) {
		this.id = id;
		this.fogColor = fogColor;
		this.previewColors = new int[] {previewTop, previewMiddle, previewAccent};
	}

	public String id() {
		return this.id;
	}

	public boolean isCustom() {
		return this != VANILLA;
	}

	public float @Nullable [] fogColor() {
		return this.fogColor;
	}

	/** Three RGB colours used to paint the tile in the SkyFX menu. */
	public int[] previewColors() {
		return this.previewColors;
	}

	public String translationKey() {
		return "skyfx.sky." + this.id;
	}

	public static SkyType byId(String id) {
		for (SkyType type : values()) {
			if (type.id.equalsIgnoreCase(id)) return type;
		}
		return AURORA;
	}
}
