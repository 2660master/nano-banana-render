package com.skyfx.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.ShapeRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.BlockOutlineRenderState;
import net.minecraft.core.BlockPos;
import net.minecraft.util.ARGB;
import net.minecraft.util.Util;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;

import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;

import com.skyfx.client.config.SkyFXConfig;

/**
 * Replaces the thin black block outline with a glowing, pulsing aura in any colour, on every block you look at.
 * It is drawn as a translucent filled box, a few wide soft line passes (the glow) and a crisp core line.
 */
public final class AuraRenderer {
	private AuraRenderer() {
	}

	/** Hooked to {@code WorldRenderEvents.BEFORE_BLOCK_OUTLINE}; returns false to suppress the vanilla outline. */
	public static boolean render(WorldRenderContext context, BlockOutlineRenderState outline) {
		SkyFXConfig config = SkyFXConfig.get();
		if (!config.auraEnabled) return true;

		Vec3 camera = context.worldState().cameraRenderState.pos;
		BlockPos pos = outline.pos();
		VoxelShape shape = outline.shape();
		if (shape.isEmpty()) return true;
		double x = pos.getX() - camera.x;
		double y = pos.getY() - camera.y;
		double z = pos.getZ() - camera.z;

		float seconds = (Util.getMillis() % 3_600_000L) / 1000.0F;
		float pulse = config.auraPulse <= 0 ? 1.0F : 0.72F + 0.28F * (float) Math.sin(seconds * 3.0F * config.auraPulse / 100.0F);
		int rgb = config.auraRainbow ? hsvToRgb((seconds * 0.12F) % 1.0F, 0.8F, 1.0F) : config.auraColor;
		int r = (rgb >> 16) & 0xFF;
		int g = (rgb >> 8) & 0xFF;
		int b = rgb & 0xFF;

		PoseStack poseStack = context.matrices();
		MultiBufferSource consumers = context.consumers();
		float baseWidth = Minecraft.getInstance().getWindow().getAppropriateLineWidth();

		// 1) translucent fill
		if (config.auraFill > 0) {
			int fillAlpha = Math.round(255 * config.auraFill / 100.0F * pulse);
			VertexConsumer fill = consumers.getBuffer(RenderTypes.debugFilledBox());
			for (AABB box : shape.toAabbs()) {
				drawBox(poseStack, fill, box.inflate(0.0025).move(x, y, z), ARGB.color(fillAlpha, r, g, b));
			}
		}

		// 2) soft glow: wide, faint line passes
		VertexConsumer glow = consumers.getBuffer(RenderTypes.linesTranslucent());
		float glowSize = config.auraGlow;
		float[][] layers = {{4.5F, 0.10F}, {3.0F, 0.18F}, {1.8F, 0.32F}};
		for (float[] layer : layers) {
			int alpha = Math.round(255 * layer[1] * pulse);
			ShapeRenderer.renderShape(poseStack, glow, shape, x, y, z, ARGB.color(alpha, r, g, b), baseWidth * (1.0F + glowSize * layer[0] * 0.5F));
		}

		// 3) crisp, bright core line
		VertexConsumer core = consumers.getBuffer(RenderTypes.lines());
		int coreRgb = brighten(rgb);
		ShapeRenderer.renderShape(poseStack, core, shape, x, y, z, ARGB.color(255, (coreRgb >> 16) & 0xFF, (coreRgb >> 8) & 0xFF, coreRgb & 0xFF), baseWidth * 1.6F);
		return false;
	}

	private static void drawBox(PoseStack poseStack, VertexConsumer consumer, AABB box, int color) {
		PoseStack.Pose pose = poseStack.last();
		float x0 = (float) box.minX, y0 = (float) box.minY, z0 = (float) box.minZ;
		float x1 = (float) box.maxX, y1 = (float) box.maxY, z1 = (float) box.maxZ;
		// down, up, north, south, west, east
		quad(pose, consumer, color, x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1);
		quad(pose, consumer, color, x0, y1, z0, x0, y1, z1, x1, y1, z1, x1, y1, z0);
		quad(pose, consumer, color, x0, y0, z0, x0, y1, z0, x1, y1, z0, x1, y0, z0);
		quad(pose, consumer, color, x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1);
		quad(pose, consumer, color, x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0);
		quad(pose, consumer, color, x1, y0, z0, x1, y1, z0, x1, y1, z1, x1, y0, z1);
	}

	private static void quad(PoseStack.Pose pose, VertexConsumer consumer, int color,
			float ax, float ay, float az, float bx, float by, float bz,
			float cx, float cy, float cz, float dx, float dy, float dz) {
		consumer.addVertex(pose, ax, ay, az).setColor(color);
		consumer.addVertex(pose, bx, by, bz).setColor(color);
		consumer.addVertex(pose, cx, cy, cz).setColor(color);
		consumer.addVertex(pose, dx, dy, dz).setColor(color);
	}

	private static int brighten(int rgb) {
		int r = (rgb >> 16) & 0xFF, g = (rgb >> 8) & 0xFF, b = rgb & 0xFF;
		r = r + (255 - r) * 2 / 5;
		g = g + (255 - g) * 2 / 5;
		b = b + (255 - b) * 2 / 5;
		return (r << 16) | (g << 8) | b;
	}

	public static int hsvToRgb(float h, float s, float v) {
		float r = channel(5, h, s, v), g = channel(3, h, s, v), b = channel(1, h, s, v);
		return (Math.round(r * 255) << 16) | (Math.round(g * 255) << 8) | Math.round(b * 255);
	}

	private static float channel(int n, float h, float s, float v) {
		float k = (n + h * 6.0F) % 6.0F;
		return v - v * s * Math.max(0.0F, Math.min(Math.min(k, 4.0F - k), 1.0F));
	}
}
