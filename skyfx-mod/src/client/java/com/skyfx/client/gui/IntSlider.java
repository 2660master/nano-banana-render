package com.skyfx.client.gui;

import java.util.function.IntConsumer;
import java.util.function.IntFunction;

import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.network.chat.Component;

/** A vanilla-style slider over an integer range with a step size. */
public class IntSlider extends AbstractSliderButton {
	private final int min;
	private final int max;
	private final int step;
	private final IntFunction<Component> label;
	private final IntConsumer onChange;

	public IntSlider(int x, int y, int width, int height, int min, int max, int step, int initial, IntFunction<Component> label, IntConsumer onChange) {
		super(x, y, width, height, Component.empty(), toSlider(initial, min, max));
		this.min = min;
		this.max = max;
		this.step = step;
		this.label = label;
		this.onChange = onChange;
		this.updateMessage();
	}

	private static double toSlider(int value, int min, int max) {
		return max == min ? 0.0 : Math.clamp((double) (value - min) / (max - min), 0.0, 1.0);
	}

	public int intValue() {
		double raw = this.min + this.value * (this.max - this.min);
		int snapped = (int) Math.round((raw - this.min) / this.step) * this.step + this.min;
		return Math.clamp(snapped, this.min, this.max);
	}

	/** Moves the handle without firing the change callback. */
	public void setIntValue(int value) {
		this.value = toSlider(value, this.min, this.max);
		this.updateMessage();
	}

	@Override
	protected void updateMessage() {
		this.setMessage(this.label.apply(this.intValue()));
	}

	@Override
	protected void applyValue() {
		this.onChange.accept(this.intValue());
	}
}
