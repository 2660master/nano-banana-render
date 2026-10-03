package com.skyfx.client.gui;

import java.util.function.BooleanSupplier;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.network.chat.Component;

import com.skyfx.client.render.AuraRenderer;

/** A coloured tile used for the sky, glint and colour pickers in the SkyFX menu. */
public class TileButton extends Button {
	public static final int ACCENT = 0xFF7CF7C5;

	private final int[] colors;
	private final boolean rainbow;
	private final BooleanSupplier selected;

	public TileButton(int x, int y, int width, int height, Component label, int[] colors, boolean rainbow, BooleanSupplier selected, OnPress onPress) {
		super(x, y, width, height, label, onPress, DEFAULT_NARRATION);
		this.colors = colors;
		this.rainbow = rainbow;
		this.selected = selected;
	}

	@Override
	protected void renderContents(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
		int x = this.getX();
		int y = this.getY();
		int w = this.getWidth();
		int h = this.getHeight();
		boolean isSelected = this.selected.getAsBoolean();
		int border = isSelected ? ACCENT : (this.isHoveredOrFocused() ? 0xFFFFFFFF : 0xFF000000);
		graphics.fill(x, y, x + w, y + h, border);
		if (isSelected) {
			graphics.fill(x + 1, y + 1, x + w - 1, y + h - 1, ACCENT);
		}
		int inset = isSelected ? 2 : 1;
		int x0 = x + inset, y0 = y + inset, x1 = x + w - inset, y1 = y + h - inset;
		if (this.rainbow) {
			int segments = 12;
			for (int i = 0; i < segments; i++) {
				int sx0 = x0 + (x1 - x0) * i / segments;
				int sx1 = x0 + (x1 - x0) * (i + 1) / segments;
				graphics.fill(sx0, y0, sx1, y1, 0xFF000000 | AuraRenderer.hsvToRgb(i / (float) segments, 0.75F, 1.0F));
			}
		} else {
			graphics.fillGradient(x0, y0, x1, y1, 0xFF000000 | this.colors[0], 0xFF000000 | this.colors[1]);
			if (this.colors.length > 2 && this.colors[2] != this.colors[1]) {
				int band = y0 + (y1 - y0) * 3 / 5;
				graphics.fillGradient(x0, band, x1, Math.min(y1, band + 3), 0xCC000000 | this.colors[2], 0x00000000 | this.colors[2]);
			}
		}
		if (!this.active) {
			graphics.fill(x0, y0, x1, y1, 0xA0000000);
		}
		Component message = this.getMessage();
		if (!message.getString().isEmpty()) {
			graphics.fillGradient(x0, Math.max(y0, y1 - 13), x1, y1, 0x00000000, 0xB0000000);
			graphics.drawString(Minecraft.getInstance().font, message, x0 + 4, y1 - 10, this.active ? 0xFFFFFFFF : 0xFF9A9A9A, true);
		}
		if (isSelected) {
			graphics.drawString(Minecraft.getInstance().font, "✔", x1 - 9, y0 + 2, ACCENT, true);
		}
	}
}
