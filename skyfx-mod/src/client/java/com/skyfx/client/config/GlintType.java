package com.skyfx.client.config;

import org.jspecify.annotations.Nullable;

import net.minecraft.resources.Identifier;

/**
 * Enchantment glints. Each custom glint is a built-in resource pack in {@code resourcepacks/<packName>/} that overrides
 * the vanilla {@code core/glint} shader. Adding a glint = adding a pack folder and an entry here.
 */
public enum GlintType {
	VANILLA("vanilla", null, 0x8A4FD8),
	PALM("palm", "palm_glint", 0x5FF2E4),
	GALAXY("galaxy", "galaxy_glint", 0x9B4FE8),
	RAINBOW("rainbow", "rainbow_glint", 0x7FD8FF),
	ICE("ice", "ice_glint", 0x6FC8FF),
	SUMMER("summer", "summer_glint", 0xFF8A3D);

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

	/** The pack's glint texture, shown on the menu tile, or null for vanilla. */
	public @Nullable Identifier guiTexture() {
		return this.packName == null ? null : Identifier.fromNamespaceAndPath("skyfx", "textures/gui/" + this.packName + ".png");
	}

	public int previewColor() {
		return this.previewColor;
	}

	public String translationKey() {
		return "skyfx.glint." + this.id;
	}
}
