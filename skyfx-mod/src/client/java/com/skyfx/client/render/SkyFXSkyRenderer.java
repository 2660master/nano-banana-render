package com.skyfx.client.render;

import java.util.EnumMap;
import java.util.Map;
import java.util.OptionalDouble;
import java.util.OptionalInt;

import com.mojang.blaze3d.buffers.GpuBuffer;
import com.mojang.blaze3d.buffers.GpuBufferSlice;
import com.mojang.blaze3d.pipeline.RenderPipeline;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.platform.DepthTestFunction;
import com.mojang.blaze3d.systems.RenderPass;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.ByteBufferBuilder;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.MeshData;
import com.mojang.blaze3d.vertex.VertexFormat;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector4f;
import org.jspecify.annotations.Nullable;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Util;
import net.minecraft.world.level.Level;

import com.skyfx.client.SkyFXClient;
import com.skyfx.client.config.SkyFXConfig;
import com.skyfx.client.config.SkyType;

/**
 * Draws the SkyFX skies. Each sky is a fully procedural fragment shader evaluated on a cube around the camera,
 * drawn in place of the vanilla sky disc during Minecraft's own "sky" frame pass.
 *
 * <p>The shader parameters travel through the standard DynamicTransforms uniform block:
 * {@code ColorModulator = (animation time, brightness, aurora palette, 0)}.
 */
public final class SkyFXSkyRenderer {
	/** The animation clock wraps after two hours so float precision in the shaders stays good. */
	private static final float TIME_WRAP = 7200.0F;
	private static final int CUBE_VERTICES = 36;

	private static final Map<SkyType, RenderPipeline> PIPELINES = new EnumMap<>(SkyType.class);
	private static final Map<SkyType, Boolean> REPORTED_INVALID = new EnumMap<>(SkyType.class);

	private static @Nullable GpuBuffer cube;
	private static float time = 20.0F;
	private static long lastNanos = -1L;
	private static boolean drawnThisFrame;

	private SkyFXSkyRenderer() {
	}

	private static RenderPipeline pipeline(SkyType type) {
		return PIPELINES.computeIfAbsent(type, t -> RenderPipeline.builder(RenderPipelines.MATRICES_PROJECTION_SNIPPET)
				.withLocation(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "pipeline/sky_" + t.id()))
				.withVertexShader(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "core/sky"))
				.withFragmentShader(Identifier.fromNamespaceAndPath(SkyFXClient.MOD_ID, "core/sky_" + t.id()))
				.withDepthWrite(false)
				.withDepthTestFunction(DepthTestFunction.NO_DEPTH_TEST)
				.withCull(false)
				.withVertexFormat(DefaultVertexFormat.POSITION, VertexFormat.Mode.TRIANGLES)
				.build());
	}

	/** True when the selected sky is a SkyFX sky and the player is in a dimension with an overworld-style sky. */
	public static boolean isCustomSkySelected() {
		ClientLevel level = Minecraft.getInstance().level;
		return SkyFXConfig.get().skyType().isCustom() && level != null && level.dimension() == Level.OVERWORLD;
	}

	/** True right after {@link #renderSky()} drew a custom sky, so the vanilla sun, moon and stars can be skipped. */
	public static boolean drewThisFrame() {
		return drawnThisFrame;
	}

	/** The horizon colour of the active custom sky, or null when the vanilla fog should be kept. */
	public static float @Nullable [] fogColor() {
		if (!SkyFXConfig.get().matchFog || !isCustomSkySelected()) return null;
		float[] fog = SkyFXConfig.get().skyType().fogColor();
		if (fog == null) return null;
		float brightness = SkyFXConfig.get().brightness / 100.0F;
		return new float[] {Math.min(fog[0] * brightness, 1.0F), Math.min(fog[1] * brightness, 1.0F), Math.min(fog[2] * brightness, 1.0F)};
	}

	/**
	 * Called at the start of the vanilla sky pass. Returns true when a SkyFX sky was drawn and the vanilla sky disc
	 * must be skipped; returns false to fall back to the vanilla sky (vanilla selected, or the shader failed to compile).
	 */
	public static boolean renderSky() {
		drawnThisFrame = false;
		advanceClock();
		SkyFXConfig config = SkyFXConfig.get();
		SkyType type = config.skyType();
		if (!type.isCustom()) return false;

		RenderPipeline pipeline = pipeline(type);
		if (!RenderSystem.getDevice().precompilePipeline(pipeline).isValid()) {
			if (REPORTED_INVALID.put(type, Boolean.TRUE) == null) {
				SkyFXClient.LOGGER.error("SkyFX sky shader '{}' failed to compile, falling back to the vanilla sky", type.id());
			}
			return false;
		}

		GpuBuffer vertices = cube();
		GpuBufferSlice transforms = RenderSystem.getDynamicUniforms().writeTransform(
				RenderSystem.getModelViewMatrix(),
				new Vector4f(time, config.brightness / 100.0F, config.auroraPalette, 0.0F),
				new Vector3f(),
				new Matrix4f());
		RenderTarget target = Minecraft.getInstance().getMainRenderTarget();
		try (RenderPass pass = RenderSystem.getDevice().createCommandEncoder().createRenderPass(
				() -> "SkyFX sky",
				target.getColorTextureView(),
				OptionalInt.empty(),
				target.getDepthTextureView(),
				OptionalDouble.empty())) {
			pass.setPipeline(pipeline);
			RenderSystem.bindDefaultUniforms(pass);
			pass.setUniform("DynamicTransforms", transforms);
			pass.setVertexBuffer(0, vertices);
			pass.draw(0, CUBE_VERTICES);
		}
		drawnThisFrame = true;
		return true;
	}

	private static void advanceClock() {
		long now = Util.getNanos();
		if (lastNanos >= 0L) {
			float dt = Math.min((now - lastNanos) / 1.0E9F, 0.25F);
			time = (time + dt * SkyFXConfig.get().speed / 100.0F) % TIME_WRAP;
		}
		lastNanos = now;
	}

	/** A cube around the camera; the vertex shader hands each fragment its view direction. */
	private static GpuBuffer cube() {
		if (cube == null || cube.isClosed()) {
			float s = 10.0F;
			float[][] corners = {
					{-s, -s, -s}, {s, -s, -s}, {s, s, -s}, {-s, s, -s},
					{-s, -s, s}, {s, -s, s}, {s, s, s}, {-s, s, s}
			};
			int[][] faces = {
					{0, 1, 2, 3}, {5, 4, 7, 6}, {4, 0, 3, 7},
					{1, 5, 6, 2}, {3, 2, 6, 7}, {4, 5, 1, 0}
			};
			try (ByteBufferBuilder bytes = ByteBufferBuilder.exactlySized(CUBE_VERTICES * DefaultVertexFormat.POSITION.getVertexSize())) {
				BufferBuilder builder = new BufferBuilder(bytes, VertexFormat.Mode.TRIANGLES, DefaultVertexFormat.POSITION);
				for (int[] face : faces) {
					int[] order = {face[0], face[1], face[2], face[0], face[2], face[3]};
					for (int index : order) {
						float[] c = corners[index];
						builder.addVertex(c[0], c[1], c[2]);
					}
				}
				try (MeshData mesh = builder.buildOrThrow()) {
					cube = RenderSystem.getDevice().createBuffer(() -> "SkyFX sky cube", GpuBuffer.USAGE_VERTEX, mesh.vertexBuffer());
				}
			}
		}
		return cube;
	}
}
