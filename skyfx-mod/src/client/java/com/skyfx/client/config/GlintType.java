package com.skyfx.client.config;

import org.jspecify.annotations.Nullable;

/**
 * Enchantment glints. Each custom glint is a built-in resource pack in {@code resourcepacks/<packName>/} that overrides
 * the vanilla {@code core/glint} shader. Adding a glint = adding a pack folder and an entry here.
 */
public enum GlintType {
	VANILLA("vanilla", null, 0x8A4FD8),
	PALM("palm", "palm_glint", 0x5FF2E4);

	private final String id;
	private final @Nullable String packName;
	private final int previewColor;

	GlintType(String id, @Nullable String packName, int previewColor) {
		this.id = id;
		this.packName = packName;
		this.previewColor = previewColor;
	}

	public String id() {
		return this.id;
	}

	/** Path of the built-in pack below {@code resourcepacks/}, or null for the untouched vanilla glint. */
	public @Nullable String packName() {
		return this.packName;
	}

	public int previewColor() {
		return this.previewColor;
	}

	public String translationKey() {
		return "skyfx.glint." + this.id;
	}
}
