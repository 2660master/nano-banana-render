package com.skyfx.client.gui;

import java.util.Locale;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;
import java.util.function.IntConsumer;
import java.util.function.IntSupplier;

import org.jspecify.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.CycleButton;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

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
	private @Nullable ColorBinding colorBinding;

	public SkyFXScreen(@Nullable Screen parent) {
		super(Component.translatable("skyfx.title"));
		this.parent = parent;
		this.pendingGlint = GlintManager.current();
	}

	private enum Tab {
		SKIES("skyfx.tab.skies", 2 * 34 + GAP + 8 + 3 * ROW),
		GLINTS("skyfx.tab.glints", 2 * 34 + GAP + 8 + 30),
		AURA("skyfx.tab.aura", 6 * ROW),
		ITEM_AURA("skyfx.tab.item_aura", 5 * ROW);

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
		this.colorBinding = null;

		this.panelW = Math.min(360, this.width - 12);
		this.panelH = 26 + ROW + 6 + this.contentHeight() + 8 + 20 + 8;
		this.panelX = (this.width - this.panelW) / 2;
		this.panelY = Math.max(4, (this.height - this.panelH) / 2);
		this.contentX = this.panelX + 8;
		this.contentW = this.panelW - 16;

		int tabY = this.panelY + 26;
		int tabW = (this.contentW - 3 * GAP) / 4;
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
			case ITEM_AURA -> this.initItemAura();
		}

		int footerY = this.panelY + this.panelH - 28;
		int half = (this.contentW - GAP) / 2;
		this.addRenderableWidget(Button.builder(Component.translatable("skyfx.button.reset"), b -> {
			SkyFXConfig.reset();
			this.pendingGlint = GlintType.PALM;
			this.rebuildWidgets();
		}).bounds(this.contentX, footerY, half, 20).build());
		this.addRenderableWidget(Button.builder(Component.translatable("skyfx.button.done"), b -> this.onClose())
				.bounds(this.contentX + half + GAP, footerY, half, 20).build());
	}

	/** The skies tab grows by the colour rows when the northern lights use a custom colour. */
	private int contentHeight() {
		return this.tab == Tab.SKIES && SkyFXConfig.get().auroraPalette == SkyFXConfig.AURORA_CUSTOM ? this.tab.contentHeight + 3 * ROW : this.tab.contentHeight;
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
				.withValues(0, 1, 2, 3, SkyFXConfig.AURORA_CUSTOM)
				.create(this.contentX, y, half, 20, Component.translatable("skyfx.option.palette"), (button, v) -> {
					boolean relayout = (v == SkyFXConfig.AURORA_CUSTOM) != (config.auroraPalette == SkyFXConfig.AURORA_CUSTOM);
					config.auroraPalette = v;
					SkyFXConfig.save();
					if (relayout) {
						this.rebuildWidgets();
					}
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
		y += ROW;
		if (config.auroraPalette == SkyFXConfig.AURORA_CUSTOM) {
			// custom northern lights colour: the same hex field, swatches and RGB sliders as the auras
			this.addColorRows(y, new ColorBinding(() -> SkyFXConfig.get().auroraColor, c -> SkyFXConfig.get().auroraColor = c,
					() -> false, v -> { }));
		}
	}

	private void addSkyTile(SkyType type, int x, int y, int width) {
		this.addRenderableWidget(new TileButton(x, y, width, 34, Component.translatable(type.translationKey()), type.previewColors(), null,
				() -> SkyFXConfig.get().skyType() == type, b -> {
					SkyFXConfig.get().sky = type.id();
					SkyFXConfig.save();
				}));
	}

	// ------------------------------------------------------------------ glints

	private void initGlints() {
		GlintType[] glints = GlintType.values();
		int perRow = (glints.length + 1) / 2;
		int tileW = (this.contentW - (perRow - 1) * GAP) / perRow;
		for (int i = 0; i < glints.length; i++) {
			GlintType type = glints[i];
			int color = type.previewColor();
			int x = this.contentX + (i % perRow) * (tileW + GAP);
			int y = this.contentY + (i / perRow) * (34 + GAP);
			this.addRenderableWidget(new TileButton(x, y, tileW, 34, Component.translatable(type.translationKey()),
					new int[] {color, darken(color), color}, type.guiTexture(), () -> this.pendingGlint == type, b -> this.pendingGlint = type));
		}
	}

	// ------------------------------------------------------------------ aura

	/** Which colour the shared hex field, swatches and RGB sliders edit (block aura or item aura). */
	private record ColorBinding(IntSupplier color, IntConsumer setColor, BooleanSupplier rainbow, Consumer<Boolean> setRainbow) {
	}

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
		CycleButton<Integer> style = CycleButton.<Integer>builder(v -> Component.translatable("skyfx.aura_style." + v), config.auraStyle)
				.withValues(0, 1, 2)
				.create(right, y, half, 20, Component.translatable("skyfx.option.aura_style"), (button, v) -> {
					config.auraStyle = v;
					SkyFXConfig.save();
				});
		style.setTooltip(Tooltip.create(Component.translatable("skyfx.option.aura_style.tooltip")));
		this.addRenderableWidget(style);
		y += ROW;

		y = this.addColorRows(y, new ColorBinding(() -> SkyFXConfig.get().auraColor, c -> SkyFXConfig.get().auraColor = c,
				() -> SkyFXConfig.get().auraRainbow, v -> SkyFXConfig.get().auraRainbow = v));
		this.addRenderableWidget(new IntSlider(right, y - ROW, half, 20, 0, 300, 10, config.auraPulse,
				v -> v == 0 ? Component.translatable("skyfx.option.pulse_off") : Component.translatable("skyfx.option.pulse", v), v -> {
					config.auraPulse = v;
					SkyFXConfig.save();
				}));
		this.addRenderableWidget(new IntSlider(this.contentX, y, half, 20, 1, 10, 1, config.auraGlow,
				v -> Component.translatable("skyfx.option.edge", v), v -> {
					config.auraGlow = v;
					SkyFXConfig.save();
				}));
		this.addRenderableWidget(new IntSlider(right, y, half, 20, 0, 60, 2, config.auraFill,
				v -> Component.translatable("skyfx.option.fill", v), v -> {
					config.auraFill = v;
					SkyFXConfig.save();
				}));
		y += ROW;
		this.addRenderableWidget(CycleButton.onOffBuilder(config.auraRainbow)
				.create(this.contentX, y, this.contentW, 20, Component.translatable("skyfx.option.aura_rainbow"), (button, v) -> {
					config.auraRainbow = v;
					SkyFXConfig.save();
				}));
	}

	private void initItemAura() {
		SkyFXConfig config = SkyFXConfig.get();
		int half = (this.contentW - GAP) / 2;
		int right = this.contentX + half + GAP;
		int y = this.contentY;

		CycleButton<Boolean> enabled = CycleButton.onOffBuilder(config.itemAuraEnabled)
				.create(this.contentX, y, half, 20, Component.translatable("skyfx.option.item_aura"), (button, v) -> {
					config.itemAuraEnabled = v;
					SkyFXConfig.save();
				});
		enabled.setTooltip(Tooltip.create(Component.translatable("skyfx.option.item_aura.tooltip")));
		this.addRenderableWidget(enabled);
		this.addRenderableWidget(CycleButton.onOffBuilder(config.itemAuraRainbow)
				.create(right, y, half, 20, Component.translatable("skyfx.option.aura_rainbow"), (button, v) -> {
					config.itemAuraRainbow = v;
					SkyFXConfig.save();
				}));
		y += ROW;

		y = this.addColorRows(y, new ColorBinding(() -> SkyFXConfig.get().itemAuraColor, c -> SkyFXConfig.get().itemAuraColor = c,
				() -> SkyFXConfig.get().itemAuraRainbow, v -> SkyFXConfig.get().itemAuraRainbow = v));
		this.addRenderableWidget(new IntSlider(right, y - ROW, half, 20, 1, 8, 1, config.itemAuraWidth,
				v -> Component.translatable("skyfx.option.item_aura_width", v), v -> {
					config.itemAuraWidth = v;
					SkyFXConfig.save();
				}));
		this.addRenderableWidget(new IntSlider(this.contentX, y, this.contentW, 20, 0, 10, 1, config.itemAuraGlow,
				v -> Component.translatable("skyfx.option.glow", v), v -> {
					config.itemAuraGlow = v;
					SkyFXConfig.save();
				}));
	}

	/**
	 * Adds the hex field (with a live swatch drawn next to it), the preset colours and the red/green/blue sliders.
	 * Leaves the slot right of the blue slider free and returns the y of the next free row.
	 */
	private int addColorRows(int y, ColorBinding binding) {
		this.colorBinding = binding;
		int half = (this.contentW - GAP) / 2;
		int right = this.contentX + half + GAP;

		EditBox hex = new EditBox(this.font, this.contentX + 24, y, half - 24, 20, Component.translatable("skyfx.option.aura_hex"));
		hex.setMaxLength(7);
		hex.setValue(String.format(Locale.ROOT, "#%06X", binding.color().getAsInt()));
		hex.setResponder(text -> {
			if (this.syncingColor) return;
			Integer parsed = parseHex(text);
			if (parsed != null) {
				this.setColor(parsed, false);
			}
		});
		this.hexBox = this.addRenderableWidget(hex);
		int swatchW = (half - (SWATCHES.length - 1) * 2) / SWATCHES.length;
		for (int i = 0; i < SWATCHES.length; i++) {
			int color = SWATCHES[i];
			this.addRenderableWidget(new TileButton(right + i * (swatchW + 2), y, swatchW, 20, Component.empty(), new int[] {color, color, color}, null,
					() -> !binding.rainbow().getAsBoolean() && binding.color().getAsInt() == color, b -> {
						this.setColor(color, true);
						this.rebuildWidgets();
					}));
		}
		y += ROW;
		this.redSlider = this.addRenderableWidget(this.channelSlider(this.contentX, y, half, "skyfx.option.red", 16));
		this.greenSlider = this.addRenderableWidget(this.channelSlider(right, y, half, "skyfx.option.green", 8));
		y += ROW;
		this.blueSlider = this.addRenderableWidget(this.channelSlider(this.contentX, y, half, "skyfx.option.blue", 0));
		return y + ROW;
	}

	private IntSlider channelSlider(int x, int y, int width, String key, int shift) {
		ColorBinding binding = this.colorBinding;
		return new IntSlider(x, y, width, 20, 0, 255, 1, (binding.color().getAsInt() >> shift) & 0xFF,
				v -> Component.translatable(key, v), v -> {
					int color = (binding.color().getAsInt() & ~(0xFF << shift)) | (v << shift);
					this.setColor(color, true);
				});
	}

	private void setColor(int color, boolean updateHex) {
		ColorBinding binding = this.colorBinding;
		if (binding == null) return;
		int rgb = color & 0xFFFFFF;
		binding.setColor().accept(rgb);
		binding.setRainbow().accept(false);
		SkyFXConfig.save();
		this.syncingColor = true;
		if (updateHex && this.hexBox != null) {
			this.hexBox.setValue(String.format(Locale.ROOT, "#%06X", rgb));
		}
		if (this.redSlider != null) this.redSlider.setIntValue((rgb >> 16) & 0xFF);
		if (this.greenSlider != null) this.greenSlider.setIntValue((rgb >> 8) & 0xFF);
		if (this.blueSlider != null) this.blueSlider.setIntValue(rgb & 0xFF);
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
		} else if (this.colorBinding != null && this.hexBox != null) {
			int x = this.contentX;
			int y = this.hexBox.getY();
			graphics.fill(x, y, x + 20, y + 20, 0xFF000000);
			int color = this.colorBinding.rainbow().getAsBoolean() ? 0xFFFFFF : this.colorBinding.color().getAsInt();
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
