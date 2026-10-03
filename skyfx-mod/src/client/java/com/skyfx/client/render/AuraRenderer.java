package com.skyfx.client.render;

import java.util.List;
import java.util.OptionalDouble;
import java.util.OptionalInt;

import com.mojang.blaze3d.buffers.GpuBuffer;
import com.mojang.blaze3d.buffers.GpuBufferSlice;
import com.mojang.blaze3d.pipeline.BlendFunction;
import com.mojang.blaze3d.pipeline.RenderPipeline;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.platform.DepthTestFunction;
import com.mojang.blaze3d.systems.RenderPass;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.ByteBufferBuilder;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.MeshData;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.vertex.VertexFormat;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector4f;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.ShapeRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.BlockOutlineRenderState;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ARGB;
import net.minecraft.util.Util;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;

import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;

import com.skyfx.client.SkyFXClient;
import com.skyfx.client.config.SkyFXConfig;

/**
 * Replaces the thin black block outline with a coloured aura on every block you look at: a translucent (pulsing)
 * filled box, or the galaxy window, plus one flat solid edge line without any glow.
 */
public final class AuraRenderer {
	private static final RenderPipeline GALAXY_PIPELINE = RenderPipeline.builder(RenderPipelines.MATRICES_PROJECTION_SNIPPET)
			.withLocation(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "pipeline/aura_galaxy"))
			.withVertexShader(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "core/aura_galaxy"))
			.withFragmentShader(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "core/aura_galaxy"))
			.withBlend(BlendFunction.TRANSLUCENT)
			.withDepthWrite(false)
			.withDepthTestFunction(DepthTestFunction.LEQUAL_DEPTH_TEST)
			.withCull(false)
			.withVertexFormat(DefaultVertexFormat.POSITION, VertexFormat.Mode.TRIANGLES)
			.build();

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

		// 1) galaxy style: the block turns into a window into space; normal style: a translucent fill
		if (config.auraStyle == 1) {
			drawGalaxy(shape.toAabbs(), x, y, z, seconds, rgb);
		} else if (config.auraFill > 0) {
			int fillAlpha = Math.round(255 * config.auraFill / 100.0F * pulse);
			VertexConsumer fill = consumers.getBuffer(RenderTypes.debugFilledBox());
			for (AABB box : shape.toAabbs()) {
				drawBox(poseStack, fill, box.inflate(0.0025).move(x, y, z), ARGB.color(fillAlpha, r, g, b));
			}
		}

		// 2) one flat, solid edge line in the exact colour: no glow, so the corners stay sharp and flat
		VertexConsumer edge = consumers.getBuffer(RenderTypes.lines());
		ShapeRenderer.renderShape(poseStack, edge, shape, x, y, z, ARGB.color(255, r, g, b), edgeWidth(baseWidth, config.auraGlow));
		return false;
	}

	private static void drawGalaxy(List<AABB> boxes, double x, double y, double z, float seconds, int rgb) {
		if (!RenderSystem.getDevice().precompilePipeline(GALAXY_PIPELINE).isValid()) return;
		int vertices = boxes.size() * 36;
		try (ByteBufferBuilder bytes = ByteBufferBuilder.exactlySized(vertices * DefaultVertexFormat.POSITION.getVertexSize())) {
			BufferBuilder builder = new BufferBuilder(bytes, VertexFormat.Mode.TRIANGLES, DefaultVertexFormat.POSITION);
			for (AABB box : boxes) {
				AABB b = box.inflate(0.003).move(x, y, z);
				float x0 = (float) b.minX, y0 = (float) b.minY, z0 = (float) b.minZ;
				float x1 = (float) b.maxX, y1 = (float) b.maxY, z1 = (float) b.maxZ;
				float[][] c = {{x0, y0, z0}, {x1, y0, z0}, {x1, y1, z0}, {x0, y1, z0}, {x0, y0, z1}, {x1, y0, z1}, {x1, y1, z1}, {x0, y1, z1}};
				int[][] faces = {{0, 1, 2, 3}, {5, 4, 7, 6}, {4, 0, 3, 7}, {1, 5, 6, 2}, {3, 2, 6, 7}, {4, 5, 1, 0}};
				for (int[] f : faces) {
					for (int i : new int[] {f[0], f[1], f[2], f[0], f[2], f[3]}) {
						builder.addVertex(c[i][0], c[i][1], c[i][2]);
					}
				}
			}
			try (MeshData mesh = builder.buildOrThrow()) {
				GpuBuffer buffer = DefaultVertexFormat.POSITION.uploadImmediateVertexBuffer(mesh.vertexBuffer());
				GpuBufferSlice transforms = RenderSystem.getDynamicUniforms().writeTransform(
						RenderSystem.getModelViewMatrix(),
						new Vector4f(seconds, ((rgb >> 16) & 0xFF) / 255.0F, ((rgb >> 8) & 0xFF) / 255.0F, (rgb & 0xFF) / 255.0F),
						new Vector3f(),
						new Matrix4f());
				RenderTarget target = Minecraft.getInstance().getMainRenderTarget();
				try (RenderPass pass = RenderSystem.getDevice().createCommandEncoder().createRenderPass(
						() -> "SkyFX galaxy aura", target.getColorTextureView(), OptionalInt.empty(), target.getDepthTextureView(), OptionalDouble.empty())) {
					pass.setPipeline(GALAXY_PIPELINE);
					RenderSystem.bindDefaultUniforms(pass);
					pass.setUniform("DynamicTransforms", transforms);
					pass.setVertexBuffer(0, buffer);
					pass.draw(0, vertices);
				}
			}
		}
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

	/** Edge thickness slider 1 - 10: 1 is the vanilla outline width, 10 is about three times as thick. */
	static float edgeWidth(float baseWidth, int setting) {
		return baseWidth * (0.75F + 0.25F * setting);
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
