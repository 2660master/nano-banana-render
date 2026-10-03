package com.skyfx.client.gui;

import java.util.Locale;

import org.jspecify.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.CycleButton;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

import com.skyfx.client.config.GlintType;
import com.skyfx.client.config.SkyFXConfig;
import com.skyfx.client.config.SkyType;
import com.skyfx.client.glint.GlintManager;

/**
 * The SkyFX menu (default key: K). The world keeps running behind it, so sky changes are visible immediately.
 */
public class SkyFXScreen extends Screen {
	private static final int ROW = 24;
	private static final int GAP = 4;
	private static final int[] SWATCHES = {0x7CF7C5, 0xFF4D6D, 0xFFB02E, 0xFFF36B, 0x4DFF88, 0x4DC3FF, 0x9B6BFF, 0xFFFFFF};
	private static Tab lastTab = Tab.SKIES;

	private final @Nullable Screen parent;
	private Tab tab = lastTab;
	private GlintType pendingGlint;
	private int panelX;
	private int panelY;
	private int panelW;
	private int panelH;
	private int contentX;
	private int contentY;
	private int contentW;
	private @Nullable EditBox hexBox;
	private @Nullable IntSlider redSlider;
	private @Nullable IntSlider greenSlider;
	private @Nullable IntSlider blueSlider;
	private boolean syncingColor;

	public SkyFXScreen(@Nullable Screen parent) {
		super(Component.translatable("skyfx.title"));
		this.parent = parent;
		this.pendingGlint = GlintManager.current();
	}

	private enum Tab {
		SKIES("skyfx.tab.skies", 2 * 34 + GAP + 8 + 3 * ROW),
		GLINTS("skyfx.tab.glints", 34 + GAP + 20 + 8 + 30),
		AURA("skyfx.tab.aura", 5 * ROW);

		final String key;
		final int contentHeight;

		Tab(String key, int contentHeight) {
			this.key = key;
			this.contentHeight = contentHeight;
		}
	}

	@Override
	protected void init() {
		this.hexBox = null;
		this.redSlider = null;
		this.greenSlider = null;
		this.blueSlider = null;

		this.panelW = Math.min(340, this.width - 12);
		this.panelH = 26 + ROW + 6 + this.tab.contentHeight + 8 + 20 + 8;
		this.panelX = (this.width - this.panelW) / 2;
		this.panelY = Math.max(4, (this.height - this.panelH) / 2);
		this.contentX = this.panelX + 8;
		this.contentW = this.panelW - 16;

		int tabY = this.panelY + 26;
		int tabW = (this.contentW - 2 * GAP) / 3;
		Tab[] tabs = Tab.values();
		for (int i = 0; i < tabs.length; i++) {
			Tab t = tabs[i];
			Button button = Button.builder(Component.translatable(t.key), b -> this.switchTab(t))
					.bounds(this.contentX + i * (tabW + GAP), tabY, tabW, 20)
					.build();
			button.active = t != this.tab;
			this.addRenderableWidget(button);
		}
		this.contentY = tabY + ROW + 6;

		switch (this.tab) {
			case SKIES -> this.initSkies();
			case GLINTS -> this.initGlints();
			case AURA -> this.initAura();
		}

		int footerY = this.panelY + this.panelH - 28;
		int half = (this.contentW - GAP) / 2;
		this.addRenderableWidget(Button.builder(Component.translatable("skyfx.button.reset"), b -> {
			SkyFXConfig.reset();
			this.pendingGlint = GlintType.RAINBOW;
			this.rebuildWidgets();
		}).bounds(this.contentX, footerY, half, 20).build());
		this.addRenderableWidget(Button.builder(Component.translatable("skyfx.button.done"), b -> this.onClose())
				.bounds(this.contentX + half + GAP, footerY, half, 20).build());
	}

	private void switchTab(Tab tab) {
		this.tab = tab;
		lastTab = tab;
		this.rebuildWidgets();
	}

	// ------------------------------------------------------------------ skies

	private void initSkies() {
		SkyFXConfig config = SkyFXConfig.get();
		int y = this.contentY;
		SkyType[] firstRow = {SkyType.AURORA, SkyType.GALAXY, SkyType.ANIME};
		int tileW = (this.contentW - 2 * GAP) / 3;
		for (int i = 0; i < firstRow.length; i++) {
			this.addSkyTile(firstRow[i], this.contentX + i * (tileW + GAP), y, tileW);
		}
		y += 34 + GAP;
		int halfTile = (this.contentW - GAP) / 2;
		this.addSkyTile(SkyType.STORM, this.contentX, y, halfTile);
		this.addSkyTile(SkyType.VANILLA, this.contentX + halfTile + GAP, y, halfTile);
		y += 34 + 8;

		int half = (this.contentW - GAP) / 2;
		int right = this.contentX + half + GAP;
		this.addRenderableWidget(new IntSlider(this.contentX, y, half, 20, 0, 300, 5, config.speed,
				v -> Component.translatable("skyfx.option.speed", v), v -> {
					config.speed = v;
					SkyFXConfig.save();
				}));
		this.addRenderableWidget(new IntSlider(right, y, half, 20, 50, 150, 5, config.brightness,
				v -> Component.translatable("skyfx.option.brightness", v), v -> {
					config.brightness = v;
					SkyFXConfig.save();
				}));
		y += ROW;
		CycleButton<Integer> palette = CycleButton.<Integer>builder(v -> Component.translatable("skyfx.palette." + v), config.auroraPalette)
				.withValues(0, 1, 2, 3)
				.create(this.contentX, y, half, 20, Component.translatable("skyfx.option.palette"), (button, v) -> {
					config.auroraPalette = v;
					SkyFXConfig.save();
				});
		palette.setTooltip(Tooltip.create(Component.translatable("skyfx.option.palette.tooltip")));
		this.addRenderableWidget(palette);
		CycleButton<Boolean> clouds = CycleButton.onOffBuilder(config.hideVanillaClouds)
				.create(right, y, half, 20, Component.translatable("skyfx.option.hide_clouds"), (button, v) -> {
					config.hideVanillaClouds = v;
					SkyFXConfig.save();
				});
		clouds.setTooltip(Tooltip.create(Component.translatable("skyfx.option.hide_clouds.tooltip")));
		this.addRenderableWidget(clouds);
		y += ROW;
		CycleButton<Boolean> fog = CycleButton.onOffBuilder(config.matchFog)
				.create(this.contentX, y, this.contentW, 20, Component.translatable("skyfx.option.match_fog"), (button, v) -> {
					config.matchFog = v;
					SkyFXConfig.save();
				});
		fog.setTooltip(Tooltip.create(Component.translatable("skyfx.option.match_fog.tooltip")));
		this.addRenderableWidget(fog);
	}

	private void addSkyTile(SkyType type, int x, int y, int width) {
		this.addRenderableWidget(new TileButton(x, y, width, 34, Component.translatable(type.translationKey()), type.previewColors(), false,
				() -> SkyFXConfig.get().skyType() == type, b -> {
					SkyFXConfig.get().sky = type.id();
					SkyFXConfig.save();
				}));
	}

	// ------------------------------------------------------------------ glints

	private void initGlints() {
		int y = this.contentY;
		GlintType[] glints = GlintType.values();
		int tileW = (this.contentW - (glints.length - 1) * GAP) / glints.length;
		for (int i = 0; i < glints.length; i++) {
			GlintType type = glints[i];
			int color = type.previewColor();
			this.addRenderableWidget(new TileButton(this.contentX + i * (tileW + GAP), y, tileW, 34, Component.translatable(type.translationKey()),
					new int[] {color, darken(color), color}, type == GlintType.RAINBOW, () -> this.pendingGlint == type, b -> this.pendingGlint = type));
		}
		y += 34 + GAP;
		Button soon = Button.builder(Component.translatable("skyfx.glint.more"), b -> { })
				.bounds(this.contentX, y, this.contentW, 20)
				.build();
		soon.active = false;
		this.addRenderableWidget(soon);
	}

	// ------------------------------------------------------------------ aura

	private void initAura() {
		SkyFXConfig config = SkyFXConfig.get();
		int half = (this.contentW - GAP) / 2;
		int right = this.contentX + half + GAP;
		int y = this.contentY;

		this.addRenderableWidget(CycleButton.onOffBuilder(config.auraEnabled)
				.create(this.contentX, y, half, 20, Component.translatable("skyfx.option.aura"), (button, v) -> {
					config.auraEnabled = v;
					SkyFXConfig.save();
				}));
		CycleButton<Boolean> rainbow = CycleButton.onOffBuilder(config.auraRainbow)
				.create(right, y, half, 20, Component.translatable("skyfx.option.aura_rainbow"), (button, v) -> {
					config.auraRainbow = v;
					SkyFXConfig.save();
				});
		this.addRenderableWidget(rainbow);
		y += ROW;

		// hex field (with a live colour swatch drawn next to it) and preset colours
		EditBox hex = new EditBox(this.font, this.contentX + 24, y, half - 24, 20, Component.translatable("skyfx.option.aura_hex"));
		hex.setMaxLength(7);
		hex.setValue(String.format(Locale.ROOT, "#%06X", config.auraColor));
		hex.setResponder(text -> {
			if (this.syncingColor) return;
			Integer parsed = parseHex(text);
			if (parsed != null) {
				this.setAuraColor(parsed, false);
			}
		});
		this.hexBox = this.addRenderableWidget(hex);
		int swatchW = (half - (SWATCHES.length - 1) * 2) / SWATCHES.length;
		for (int i = 0; i < SWATCHES.length; i++) {
			int color = SWATCHES[i];
			this.addRenderableWidget(new TileButton(right + i * (swatchW + 2), y, swatchW, 20, Component.empty(), new int[] {color, color, color}, false,
					() -> !SkyFXConfig.get().auraRainbow && SkyFXConfig.get().auraColor == color, b -> {
						config.auraRainbow = false;
						this.setAuraColor(color, true);
						this.rebuildWidgets();
					}));
		}
		y += ROW;

		this.redSlider = this.addRenderableWidget(this.channelSlider(this.contentX, y, half, "skyfx.option.red", 16));
		this.greenSlider = this.addRenderableWidget(this.channelSlider(right, y, half, "skyfx.option.green", 8));
		y += ROW;
		this.blueSlider = this.addRenderableWidget(this.channelSlider(this.contentX, y, half, "skyfx.option.blue", 0));
		this.addRenderableWidget(new IntSlider(right, y, half, 20, 0, 300, 10, config.auraPulse,
				v -> v == 0 ? Component.translatable("skyfx.option.pulse_off") : Component.translatable("skyfx.option.pulse", v), v -> {
					config.auraPulse = v;
					SkyFXConfig.save();
				}));
		y += ROW;
		this.addRenderableWidget(new IntSlider(this.contentX, y, half, 20, 1, 10, 1, config.auraGlow,
				v -> Component.translatable("skyfx.option.glow", v), v -> {
					config.auraGlow = v;
					SkyFXConfig.save();
				}));
		this.addRenderableWidget(new IntSlider(right, y, half, 20, 0, 60, 2, config.auraFill,
				v -> Component.translatable("skyfx.option.fill", v), v -> {
					config.auraFill = v;
					SkyFXConfig.save();
				}));
	}

	private IntSlider channelSlider(int x, int y, int width, String key, int shift) {
		SkyFXConfig config = SkyFXConfig.get();
		return new IntSlider(x, y, width, 20, 0, 255, 1, (config.auraColor >> shift) & 0xFF,
				v -> Component.translatable(key, v), v -> {
					int color = (SkyFXConfig.get().auraColor & ~(0xFF << shift)) | (v << shift);
					this.setAuraColor(color, true);
				});
	}

	private void setAuraColor(int color, boolean updateHex) {
		SkyFXConfig config = SkyFXConfig.get();
		config.auraColor = color & 0xFFFFFF;
		config.auraRainbow = false;
		SkyFXConfig.save();
		this.syncingColor = true;
		if (updateHex && this.hexBox != null) {
			this.hexBox.setValue(String.format(Locale.ROOT, "#%06X", config.auraColor));
		}
		if (this.redSlider != null) this.redSlider.setIntValue((config.auraColor >> 16) & 0xFF);
		if (this.greenSlider != null) this.greenSlider.setIntValue((config.auraColor >> 8) & 0xFF);
		if (this.blueSlider != null) this.blueSlider.setIntValue(config.auraColor & 0xFF);
		this.syncingColor = false;
	}

	private static @Nullable Integer parseHex(String text) {
		String s = text.trim();
		if (s.startsWith("#")) s = s.substring(1);
		if (s.length() != 6) return null;
		try {
			return Integer.parseInt(s, 16);
		} catch (NumberFormatException e) {
			return null;
		}
	}

	private static int darken(int rgb) {
		return ((rgb >> 1) & 0x7F7F7F);
	}

	// ------------------------------------------------------------------ rendering

	@Override
	public void renderBackground(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
		if (this.minecraft.level == null) {
			super.renderBackground(graphics, mouseX, mouseY, partialTick);
		}
		graphics.fill(this.panelX - 1, this.panelY - 1, this.panelX + this.panelW + 1, this.panelY + this.panelH + 1, 0xFF000000);
		graphics.fill(this.panelX, this.panelY, this.panelX + this.panelW, this.panelY + this.panelH, 0xC80B0C14);
		graphics.renderOutline(this.panelX + 1, this.panelY + 1, this.panelW - 2, this.panelH - 2, 0x30FFFFFF);
	}

	@Override
	public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
		super.render(graphics, mouseX, mouseY, partialTick);
		Component title = Component.literal("Sky").append(Component.literal("FX").withStyle(ChatFormatting.AQUA)).withStyle(ChatFormatting.BOLD);
		graphics.drawString(this.font, title, this.contentX, this.panelY + 9, 0xFFFFFFFF, true);
		Component subtitle = Component.translatable("skyfx.subtitle");
		graphics.drawString(this.font, subtitle, this.panelX + this.panelW - 8 - this.font.width(subtitle), this.panelY + 9, 0xFFA9ABC0, true);

		if (this.tab == Tab.GLINTS) {
			int y = this.contentY + 34 + GAP + 20 + 8;
			graphics.drawString(this.font, Component.translatable("skyfx.glint.info1"), this.contentX, y, 0xFFA9ABC0, true);
			graphics.drawString(this.font, Component.translatable("skyfx.glint.info2"), this.contentX, y + 11, 0xFFA9ABC0, true);
			if (this.pendingGlint != GlintManager.current()) {
				graphics.drawString(this.font, Component.translatable("skyfx.glint.pending").withStyle(ChatFormatting.YELLOW), this.contentX, y + 22, 0xFFFFFFFF, true);
			}
		} else if (this.tab == Tab.AURA && this.hexBox != null) {
			SkyFXConfig config = SkyFXConfig.get();
			int x = this.contentX;
			int y = this.hexBox.getY();
			graphics.fill(x, y, x + 20, y + 20, 0xFF000000);
			int color = config.auraRainbow ? 0xFFFFFF : config.auraColor;
			graphics.fill(x + 1, y + 1, x + 19, y + 19, 0xFF000000 | color);
		}
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void onClose() {
		SkyFXConfig.save();
		GlintType glint = this.pendingGlint;
		this.minecraft.setScreen(this.parent);
		if (glint != GlintManager.current()) {
			GlintManager.apply(glint);
		}
	}
}
